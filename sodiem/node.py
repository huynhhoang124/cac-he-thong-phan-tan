"""Trạng thái của một node và cách gọi node khác (chỉ qua HTTP)."""
from __future__ import annotations

import asyncio
import os
from urllib.parse import urlparse

import httpx

from .authz import Capabilities
from .crypto import Identity
from .monitor import Detector, Firewall
from .trust import AuditChain, Keyring

NODE_ID = os.getenv("NODE_ID", "node-dev")


def _peer(entry: str) -> tuple[str, str]:
    """'http://node-b:8000' (tên = hostname) hoặc 'node-b=http://localhost:8002'."""
    name, _, url = entry.rpartition("=") if "=" in entry else (urlparse(entry).hostname, "", entry)
    return name, url.rstrip("/")


PEERS = dict(_peer(v.strip()) for v in os.getenv("PEERS", "").split(",") if v.strip())
TIMEOUT = float(os.getenv("PEER_TIMEOUT", "1.5"))

identity = Identity(NODE_ID, os.getenv("DATA_DIR"))
keyring = Keyring(NODE_ID, identity.public_key)
audit = AuditChain(NODE_ID)
detector = Detector(identity, keyring)
firewall = Firewall()
caps = Capabilities(identity, keyring)

_local_app = None


def bind(app) -> None:
    global _local_app
    _local_app = app


def nodes() -> list[str]:
    return [NODE_ID, *PEERS]


def _client(node: str) -> httpx.AsyncClient:
    if node == NODE_ID:
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=_local_app), base_url="http://localhost", timeout=TIMEOUT)
    return httpx.AsyncClient(base_url=PEERS[node], timeout=TIMEOUT)


async def call(node: str, method: str, path: str, json: dict | None = None, **kw) -> tuple[int | None, dict]:
    """Gọi một node. Node chết → (None, {...}) thay vì ném lỗi: partial failure là bình thường."""
    try:
        async with _client(node) as client:
            r = await client.request(method, path, json=json, **kw)
            try:
                return r.status_code, r.json()
            except ValueError:
                return r.status_code, {}
    except httpx.HTTPError as exc:
        return None, {"detail": f"{node} không phản hồi ({type(exc).__name__})"}


async def call_many(targets: list[str], method: str, path: str, json: dict | None = None) -> dict[str, tuple[int | None, dict]]:
    results = await asyncio.gather(*(call(n, method, path, json) for n in targets))
    return dict(zip(targets, results))


async def ensure_key(node: str) -> None:
    """Học khóa của peer (trong cấu hình cluster) lần đầu cần đến."""
    if keyring.key_of(node) is None and node in PEERS:
        status, data = await call(node, "GET", "/identity")
        if status == 200 and data.get("node_id") == node:
            keyring.learn(node, data["public_key"])


def reset() -> None:
    audit.clear()
    detector.reset()
    firewall.reset()


async def sense(event: dict) -> list[dict]:
    """Sensor cục bộ quan sát một sự kiện. Cảnh báo sinh ra được ký và gửi song song
    tới peer, một lần, không gửi lại: peer chết chỉ làm mất báo cáo của nó."""
    out = []
    for alert in detector.observe(event):
        p = alert["payload"]
        audit.append("local_alert", {"kind": p["kind"], "source": p["source"]})
        replies = await call_many(list(PEERS), "POST", "/peer/alert", alert)
        out.append({**p, "peers": {n: ({"down": True} if code is None else data) for n, (code, data) in replies.items()}})
    return out
