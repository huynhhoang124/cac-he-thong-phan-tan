"""Sổ điểm DS: một node. API người dùng nằm ở gradebook.py; ở đây chỉ có phần giữa các node."""
from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import gradebook, node
from .node import NODE_ID, audit, detector, firewall, identity, keyring

STATIC = Path(__file__).parent / "static"
# Lưu lượng nội bộ giữa các node đã có chữ ký; gateway chỉ lọc lưu lượng từ client.
UNFILTERED = ("/peer/", "/identity", "/health", "/status", "/static/")

app = FastAPI(title="Sổ điểm DS", version="1.0.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(","))
app.mount("/static", StaticFiles(directory=STATIC), name="static")
node.bind(app)


@app.middleware("http")
async def gateway(request: Request, call_next):
    path = request.url.path
    if path != "/" and not path.startswith(UNFILTERED) and not request.headers.get("x-hop"):
        source = request.client.host if request.client else "unknown"
        blocked = firewall.admit(source, int(request.headers.get("content-length") or 0))
        if blocked:
            return JSONResponse({"detail": f"Quá nhiều yêu cầu: {blocked[1]}"}, status_code=blocked[0])
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "node_id": NODE_ID, "time": time.time()}


@app.get("/identity")
async def get_identity():
    return {"node_id": NODE_ID, "public_key": identity.public_key, "fingerprint": identity.fingerprint}


# shortcut: /status không xác thực để peer gọi nhau; production cần mTLS giữa các node.
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
        "grades_version": gradebook.book["version"],
        "tickets": len(gradebook.book["tickets"]),
    }


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


app.include_router(gradebook.router)
