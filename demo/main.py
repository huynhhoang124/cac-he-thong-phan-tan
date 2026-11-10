"""TrustMesh node: API thật của một node. Câu chuyện trình diễn nằm ở scenarios.py."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import node
from .authz import evaluate
from .node import NODE_ID, PEERS, audit, caps, detector, firewall, identity, keyring

STATIC = Path(__file__).parent / "static"
# Lưu lượng nội bộ giữa các node đã có chữ ký; gateway chỉ lọc lưu lượng từ client.
UNFILTERED = ("/peer/", "/identity", "/health", "/status", "/static/")

app = FastAPI(title="TrustMesh", version="2.0.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(","))
app.mount("/static", StaticFiles(directory=STATIC), name="static")
node.bind(app)


@app.middleware("http")
async def gateway(request: Request, call_next):
    path = request.url.path
    if path != "/" and not path.startswith(UNFILTERED):
        source = request.client.host if request.client else "unknown"
        blocked = firewall.admit(source, int(request.headers.get("content-length") or 0))
        if blocked:
            return JSONResponse({"detail": f"Firewall: {blocked[1]}"}, status_code=blocked[0])
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


class AccessCheck(BaseModel):
    subject: str = Field(max_length=64)
    resource: str = Field(max_length=64)
    action: Literal["read", "write", "delete"]
    zone: Literal["campus", "vpn", "public"] = "campus"
    capability: dict | None = None
    claims: dict | None = None  # client tự khai thuộc tính → luôn bị bỏ qua
    source: str | None = Field(None, max_length=64)  # IP client mô phỏng; mặc định là IP thật của kết nối


class Issue(BaseModel):
    issuer: str = Field(max_length=64)
    subject: str = Field(max_length=64)
    resource: str = Field(max_length=64)
    actions: list[Literal["read", "write", "delete"]] = Field(min_length=1)
    ttl: int = Field(300, ge=5, le=3600)
    may_delegate: bool = False


class Delegate(BaseModel):
    parent: dict
    holder: str = Field(max_length=64)
    subject: str = Field(max_length=64)
    actions: list[Literal["read", "write", "delete"]] = Field(min_length=1)
    ttl: int = Field(120, ge=5, le=3600)
    may_delegate: bool = False


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "node_id": NODE_ID, "time": time.time()}


@app.get("/identity")
async def get_identity():
    return {"node_id": NODE_ID, "public_key": identity.public_key, "fingerprint": identity.fingerprint}


@app.get("/status")
async def status():
    return {
        "node_id": NODE_ID,
        "fingerprint": identity.fingerprint,
        "keyring": keyring.members(),
        "audit": audit.verify(),
        "audit_tail": audit.tail(8),
        "incidents": list(detector.incidents.values()),
        "alerts": len(detector.alerts),
    }


@app.get("/cluster")
async def cluster():
    results = await node.call_many(node.nodes(), "GET", "/status")
    out = []
    for name, (code, data) in results.items():
        if code == 200:
            await node.ensure_key(name)
            out.append({"reachable": True, **data})
        else:
            out.append({"node_id": name, "reachable": False})
    return {"self": NODE_ID, "nodes": out}


# ---------- 9.5 Authorization ----------

@app.post("/access/check")
async def access_check(req: AccessCheck, request: Request):
    if req.capability:
        await node.ensure_key(str(req.capability.get("payload", {}).get("node", "")))
        decision = caps.check(req.capability, req.subject, req.resource, req.action)
    else:
        decision = evaluate(req.subject, req.resource, req.action, req.zone)
    result = {**decision.dict(), "node_id": NODE_ID}
    if req.claims:
        result["ignored_claims"] = req.claims
    audit.append("access", {"subject": req.subject, "resource": req.resource, "action": req.action,
                            "allowed": decision.allowed, "model": decision.model})
    # Mỗi quyết định cũng là một sự kiện cho sensor của chính node này (9.6).
    source = req.source or (request.client.host if request.client else "unknown")
    result["alerts"] = await sense({"source": source, "actor": req.subject, "path": f"/{req.resource}",
                                    "decision": "allowed" if decision.allowed else "denied"})
    return result


@app.post("/capabilities/issue")
async def issue(req: Issue):
    try:
        cap = caps.issue(req.issuer, req.subject, req.resource, req.actions, req.ttl, req.may_delegate)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    audit.append("capability_issued", {k: cap["payload"][k] for k in ("issuer", "subject", "resource", "actions")})
    return cap


@app.post("/capabilities/delegate")
async def delegate(req: Delegate):
    await node.ensure_key(str(req.parent.get("payload", {}).get("node", "")))
    try:
        cap = caps.delegate(req.parent, req.holder, req.subject, req.actions, req.ttl, req.may_delegate)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    audit.append("capability_delegated", {k: cap["payload"][k] for k in ("issuer", "subject", "actions", "depth")})
    return cap


# ---------- 9.6 Monitoring ----------

async def sense(event: dict) -> list[dict]:
    """Sensor cục bộ quan sát một sự kiện. Cảnh báo sinh ra được ký và gửi song song
    tới peer, một lần, không gửi lại: peer chết chỉ làm mất báo cáo của nó."""
    out = []
    for alert in detector.observe(event):
        p = alert["payload"]
        audit.append("local_alert", {"kind": p["kind"], "source": p["source"]})
        replies = await node.call_many(list(PEERS), "POST", "/peer/alert", alert)
        out.append({**p, "peers": {n: ({"down": True} if code is None else data) for n, (code, data) in replies.items()}})
    return out


@app.post("/peer/alert")
async def peer_alert(signed: dict):
    payload = signed.get("payload") or {}
    reporter = str(payload.get("reporter", ""))
    if reporter == NODE_ID:
        raise HTTPException(400, "không nhận cảnh báo mang tên chính mình từ bên ngoài")
    await node.ensure_key(reporter)
    try:
        result = detector.accept(signed)
    except (ValueError, KeyError, TypeError) as exc:
        audit.append("alert_rejected", {"claimed_reporter": reporter, "reason": str(exc)})
        raise HTTPException(400, f"Từ chối cảnh báo: {exc}") from exc
    audit.append("peer_alert", {"reporter": reporter, "source": result["source"], "confirmed": result["confirmed"]})
    return {**result, "node_id": NODE_ID}


# ---------- 9.4 Trust: audit ----------

@app.get("/audit")
async def audit_records():
    return {"verification": audit.verify(), "records": audit.tail(50)}


@app.get("/audit/verify")
async def audit_verify():
    return audit.verify()


@app.post("/audit/tamper")
async def audit_tamper(index: int = 0):
    record = audit.tamper(index)
    if record is None:
        raise HTTPException(404, "không có bản ghi để sửa")
    return {"tampered": record, "verification": audit.verify()}


# ---------- Điều khiển demo ----------

@app.post("/peer/reset")
async def peer_reset():
    node.reset()
    reset_story()
    return {"reset": NODE_ID}


@app.post("/admin/reset")
async def admin_reset():
    node.reset()
    reset_story()
    results = await node.call_many(list(PEERS), "POST", "/peer/reset")
    return {"reset": [NODE_ID, *(n for n, (code, _) in results.items() if code == 200)]}


from .scenarios import reset as reset_story, router  # noqa: E402

app.include_router(router)
