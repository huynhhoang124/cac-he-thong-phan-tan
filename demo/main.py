from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .audit import AuditChain
from .models import (
    AccessRequest,
    CapabilityDelegateRequest,
    CapabilityIssueRequest,
    SecurityEvent,
    SignedAlert,
    SybilRequest,
)
from .monitoring import CollaborativeDetector
from .policy import CapabilityService, PolicyEngine
from .security import NodeIdentity


NODE_ID = os.getenv("NODE_ID", "node-dev")
PEERS = [value.strip().rstrip("/") for value in os.getenv("PEERS", "").split(",") if value.strip()]
ALLOWED_HOSTS = [value.strip() for value in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")]
STATIC_DIR = Path(__file__).parent / "static"

identity = NodeIdentity(NODE_ID, os.getenv("DATA_DIR", "/data"))
policy = PolicyEngine()
capabilities = CapabilityService(identity, policy)
audit = AuditChain(NODE_ID)
detector = CollaborativeDetector(NODE_ID, identity)

app = FastAPI(
    title="TrustMesh",
    version="1.0.0",
    debug=False,
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "1") == "1" else None,
    redoc_url=None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

rate_windows: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def application_gateway(request: Request, call_next):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 64_000:
        return JSONResponse({"detail": "Payload vượt giới hạn application gateway"}, status_code=413)
    source = request.client.host if request.client else "unknown"
    now = time.time()
    window = rate_windows[source]
    while window and window[0] < now - 10:
        window.popleft()
    if len(window) >= 80:
        return JSONResponse({"detail": "Rate limit của application gateway"}, status_code=429)
    window.append(now)
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self' http://localhost:8001 http://localhost:8002 http://localhost:8003"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "node_id": NODE_ID, "fingerprint": identity.fingerprint, "time": time.time()}


@app.get("/identity")
async def get_identity():
    return {"node_id": NODE_ID, "public_key": identity.public_key_b64, "fingerprint": identity.fingerprint}


@app.get("/cluster")
async def cluster():
    async def probe(peer: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(f"{peer}/health")
                response.raise_for_status()
                return {"url": peer, "reachable": True, **response.json()}
        except (httpx.HTTPError, ValueError):
            return {"url": peer, "reachable": False}

    peers = await asyncio.gather(*(probe(peer) for peer in PEERS))
    return {"self": await health(), "peers": peers}


@app.post("/access/check")
async def access_check(request: AccessRequest):
    if request.capability:
        decision = capabilities.verify(
            request.capability,
            subject=request.subject.subject_id,
            resource=request.resource.resource_id,
            action=request.action,
        )
    else:
        decision = policy.evaluate(request)
    audit.append("access_decision", {"subject": request.subject.subject_id, "resource": request.resource.resource_id, "action": request.action, "allowed": decision.allowed, "reason": decision.reason})
    return {"allowed": decision.allowed, "reason": decision.reason, "node_id": NODE_ID}


@app.post("/capabilities/issue")
async def issue_capability(request: CapabilityIssueRequest):
    try:
        capability = capabilities.issue(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    audit.append("capability_issued", {"issuer": request.issuer.subject_id, "subject": request.subject_id, "resource": request.resource.resource_id, "actions": request.actions})
    return capability


@app.post("/capabilities/delegate")
async def delegate_capability(request: CapabilityDelegateRequest):
    try:
        capability = capabilities.delegate(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    audit.append("capability_delegated", {"subject": request.subject_id, "actions": request.actions})
    return capability


@app.post("/capabilities/verify")
async def verify_capability(capability: dict):
    decision = capabilities.verify(capability)
    return {"valid": decision.allowed, "reason": decision.reason}


async def broadcast_alert(alert: dict) -> None:
    async with httpx.AsyncClient(timeout=1.5) as client:
        await asyncio.gather(
            *(client.post(f"{peer}/alerts/receive", json=alert) for peer in PEERS),
            return_exceptions=True,
        )


@app.post("/events")
async def ingest_event(event: SecurityEvent):
    alerts = detector.observe(event)
    audit.append("security_event", event.model_dump())
    for alert in alerts:
        audit.append("local_alert", alert["payload"])
        asyncio.create_task(broadcast_alert(alert))
    return {"accepted": True, "node_id": NODE_ID, "alerts": [item["payload"] for item in alerts]}


@app.post("/alerts/receive")
async def receive_alert(alert: SignedAlert):
    signed = alert.model_dump()
    payload = signed["payload"]
    if payload.get("reporter") == NODE_ID:
        raise HTTPException(status_code=400, detail="Self report không được nhận qua peer API")
    reporter = payload.get("reporter")
    public_key = None
    async with httpx.AsyncClient(timeout=1.5) as client:
        for peer in PEERS:
            try:
                response = await client.get(f"{peer}/identity")
                data = response.json()
                if data.get("node_id") == reporter:
                    public_key = data.get("public_key")
                    break
            except (httpx.HTTPError, ValueError):
                continue
    if public_key != signed["public_key"] or not NodeIdentity.verify(public_key or "", payload, signed["signature"]):
        raise HTTPException(status_code=400, detail="Chữ ký alert không hợp lệ")
    result = detector.accept_verified_alert(signed)
    audit.append("peer_alert", {"reporter": reporter, **result})
    return result


@app.get("/monitoring")
async def monitoring_snapshot():
    return detector.snapshot()


@app.get("/audit")
async def audit_records():
    return {"verification": audit.verify(), "records": audit.list()}


@app.post("/audit/tamper-demo")
async def tamper_audit():
    changed = audit.tamper_for_demo()
    return {"tampered": changed, "verification": audit.verify()}


@app.post("/audit/reset")
async def reset_audit():
    audit.clear()
    return {"reset": True, "verification": audit.verify()}


@app.post("/demo/sybil")
async def demo_sybil(request: SybilRequest):
    fingerprint = "attacker-device-fingerprint"
    naive = [f"sybil-{index}" for index in range(request.count)]
    accepted_resistant: list[str] = []
    seen_fingerprints: set[str] = set()
    for identity_index in range(request.count):
        candidate = f"sybil-{identity_index}"
        enough_stake = request.stake_per_identity >= 10
        unique_physical_identity = fingerprint not in seen_fingerprints
        if enough_stake and unique_physical_identity:
            accepted_resistant.append(candidate)
            seen_fingerprints.add(fingerprint)
    result = {
        "requested": request.count,
        "naive_accepted": naive,
        "resistant_accepted": accepted_resistant,
        "rule": "unique fingerprint và stake >= 10",
        "lesson": "Ràng buộc tài nguyên làm nhiều identity trở nên tốn kém, nhưng không loại bỏ mọi Sybil attack.",
    }
    audit.append("sybil_simulation", result)
    return result


def demo_subjects_resources() -> tuple[dict, dict]:
    alice = {"subject_id": "alice", "role": "teacher", "department": "cs", "courses": ["distributed-systems"], "clearance": "confidential"}
    bob = {"subject_id": "bob", "role": "student", "department": "cs", "courses": ["distributed-systems"], "clearance": "confidential"}
    mallory = {"subject_id": "mallory", "role": "guest", "department": "public", "courses": [], "clearance": "public"}
    grades = {"resource_id": "grades-ds-2026", "owner": "registrar", "classification": "confidential", "department": "cs", "course": "distributed-systems"}
    return {"alice": alice, "bob": bob, "mallory": mallory}, {"grades": grades}


@app.post("/demo/authorization")
async def demo_authorization():
    subjects, resources = demo_subjects_resources()
    alice_request = AccessRequest(subject=subjects["alice"], resource=resources["grades"], action="read", environment={"network_zone": "campus", "hour": 10})
    mallory_request = AccessRequest(subject=subjects["mallory"], resource=resources["grades"], action="read")
    alice_decision = policy.evaluate(alice_request)
    mallory_decision = policy.evaluate(mallory_request)
    capability = capabilities.issue(CapabilityIssueRequest(issuer=subjects["alice"], subject_id="bob", resource=resources["grades"], actions=["read"], ttl_seconds=300, may_delegate=False))
    bob_read = capabilities.verify(capability, subject="bob", resource="grades-ds-2026", action="read")
    bob_write = capabilities.verify(capability, subject="bob", resource="grades-ds-2026", action="write")
    result = {
        "abac": {
            "alice_read": {"allowed": alice_decision.allowed, "reason": alice_decision.reason},
            "mallory_read": {"allowed": mallory_decision.allowed, "reason": mallory_decision.reason},
        },
        "delegation": {
            "capability": capability,
            "bob_read": {"allowed": bob_read.allowed, "reason": bob_read.reason},
            "bob_write": {"allowed": bob_write.allowed, "reason": bob_write.reason},
        },
    }
    audit.append("authorization_scenario", {"alice_allowed": alice_decision.allowed, "mallory_allowed": mallory_decision.allowed, "bob_read": bob_read.allowed, "bob_write": bob_write.allowed})
    return result


@app.post("/demo/cids")
async def demo_cids():
    targets = [f"http://{NODE_ID}:8000"] if NODE_ID != "node-dev" else []
    targets.extend(PEERS)
    events = [
        SecurityEvent(event_id=str(uuid.uuid4()), source="203.0.113.77", actor=f"sybil-{index}", action="read", resource="grades-ds-2026", decision="denied", ground_truth="malicious").model_dump()
        for index in range(5)
    ]
    results: list[dict] = []
    if not targets:
        for raw in events:
            alerts = detector.observe(SecurityEvent(**raw))
            results.append({"node": NODE_ID, "alerts": [a["payload"] for a in alerts]})
    else:
        async with httpx.AsyncClient(timeout=2.0) as client:
            for target in targets:
                delivered = 0
                for event in events:
                    try:
                        response = await client.post(f"{target}/events", json=event)
                        if response.is_success:
                            delivered += 1
                    except httpx.HTTPError:
                        break
                results.append({"node": target, "events_delivered": delivered})
    await asyncio.sleep(0.5)
    return {"scenario": "correlated denied-access and Sybil burst", "deliveries": results, "local_snapshot": detector.snapshot()}
