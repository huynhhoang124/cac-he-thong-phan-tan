"""Sổ điểm DS: API người dùng.

- Đăng nhập: node kiểm mật khẩu rồi ký phiên (Ed25519). Node nào trong cluster cũng tự kiểm được phiên.
- Mỗi yêu cầu được chia vòng (round-robin) sang node khác; node chết thì bỏ qua (partial failure).
- Quyền: directory (ABAC/MAC/...) trước, không được thì thử các quyền được chia sẻ (capability).
- Mỗi quyết định ghi audit và đưa cho sensor; cảnh báo chỉ thành sự cố khi ≥2 node cùng báo.
- Điểm và quyền chia sẻ được ký rồi nhân bản sang peer; peer kiểm chữ ký trước khi ghi.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import itertools
import json
import os
import time
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from . import node
from .authz import SUBJECTS, evaluate
from .crypto import verify
from .node import NODE_ID, PEERS, audit, caps, identity, keyring

router = APIRouter()

RESOURCE = "grades-ds"
SESSION_TTL = 8 * 3600
SEED = {"bob": 7.5, "carol": 8.0, "dave": 6.5, "erin": 9.0}
PROFILES = {
    "alice": ("Alice", "Giảng viên môn DS"),
    "bob": ("Bob", "Sinh viên, trợ giảng"),
    "carol": ("Carol", "Sinh viên"),
    "mallory": ("Mallory", "Khách"),
    "root": ("Quản trị", "Quản trị hệ thống"),
}
_SALT = b"sodiem-ds"
# Tài khoản thử nghiệm (xem README). Chỉ giữ hash trong bộ nhớ.
_PASSWORDS = {u: hashlib.pbkdf2_hmac("sha256", os.getenv(f"PW_{u.upper()}", f"{u}123").encode(), _SALT, 100_000)
              for u in PROFILES}

book: dict = {}


def reset() -> None:
    book.update(grades=dict(SEED), version=0, tickets=[])


reset()

# ---------------- phiên đăng nhập ----------------


def make_token(user: str) -> str:
    signed = identity.signed({"user": user, "exp": int(time.time()) + SESSION_TTL, "node": NODE_ID})
    return base64.urlsafe_b64encode(json.dumps(signed).encode()).decode()


async def session_user(authorization: str) -> str:
    try:
        signed = json.loads(base64.urlsafe_b64decode(authorization.removeprefix("Bearer ").encode()))
        p, sig = signed["payload"], signed["signature"]
        await node.ensure_key(str(p["node"]))
        key = keyring.key_of(str(p["node"]))
        if key and verify(key, p, sig) and p["exp"] > time.time() and p["user"] in PROFILES:
            return p["user"]
    except (ValueError, KeyError, TypeError):
        pass
    raise HTTPException(401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")


# shortcut: sensor gom theo "user@ip" vì khi chạy thử mọi người dùng chung 127.0.0.1; IDS thật gom theo IP/thiết bị.
def client_ip(request: Request) -> str:
    # shortcut: tin x-client khi có x-hop (request từ peer); production cần mTLS để chỉ peer gửi được header này.
    if request.headers.get("x-hop"):
        return request.headers.get("x-client", "unknown")
    return request.client.host if request.client else "unknown"


# ---------------- chia vòng giữa các node ----------------

_turn = itertools.count()


async def route(request: Request, body: dict | None = None) -> dict | None:
    """Chuyển yêu cầu sang node kế tiếp. None nghĩa là node này tự xử lý."""
    if request.headers.get("x-hop"):
        return None
    order = node.nodes()
    start = next(_turn) % len(order)
    headers = {"x-hop": "1", "x-client": client_ip(request),
               "authorization": request.headers.get("authorization", "")}
    for n in order[start:] + order[:start]:
        if n == NODE_ID:
            return None
        code, data = await node.call(n, request.method, request.url.path, json=body, headers=headers,
                                     timeout=node.TIMEOUT * 3)
        if code is None:
            continue  # node chết → thử node kế tiếp
        if code != 200:
            raise HTTPException(code, data.get("detail", f"{n} trả {code}"))
        return data
    return None


# ---------------- quyết định truy cập ----------------


def granted(user: str, action: str) -> tuple[bool, str]:
    """Không ghi log: dùng để giao diện biết nên hiện nút nào."""
    if evaluate(user, RESOURCE, action).allowed:
        return True, "directory"
    for cap in book["tickets"]:
        if caps.check(cap, user, RESOURCE, action).allowed:
            return True, f"chia sẻ bởi {cap['payload']['issuer']}"
    return False, ""


async def decide(user: str, action: str, ip: str, path: str = "/grades-ds") -> dict:
    d = evaluate(user, RESOURCE, action)
    if not d.allowed:
        for cap in book["tickets"]:
            if cap["payload"]["subject"] != user:
                continue
            d = caps.check(cap, user, RESOURCE, action)  # lý do từ chối của vé cũng có ích cho người dùng
            if d.allowed:
                break
    audit.append("access", {"subject": user, "resource": RESOURCE, "action": action,
                            "allowed": d.allowed, "model": d.model})
    await node.sense({"source": f"{user}@{ip}", "actor": user, "path": path, "decision": "allowed" if d.allowed else "denied"})
    return d.dict()


def denied(d: dict) -> HTTPException:
    return HTTPException(403, f"Bạn không có quyền này ({d['model']}: {d['reason']})")


# ---------------- API ----------------


class Login(BaseModel):
    user: str = Field(max_length=64)
    password: str = Field(max_length=128)


class Score(BaseModel):
    score: float = Field(ge=0, le=10)


class Share(BaseModel):
    to: str = Field(max_length=64)
    actions: list[Literal["read", "write", "delete"]] = Field(min_length=1)
    minutes: int = Field(60, ge=1, le=60 * 24)
    may_delegate: bool = False


def profile(user: str) -> dict:
    name, title = PROFILES[user]
    can = {a: granted(user, a)[0] for a in ("read", "write")}
    return {"user": user, "name": name, "title": title, "admin": SUBJECTS[user]["role"] == "admin",
            "can_read": can["read"], "can_write": can["write"],
            "can_share": can["read"] and (evaluate(user, RESOURCE, "read").allowed or any(
                c["payload"]["subject"] == user and c["payload"]["may_delegate"] for c in book["tickets"]
                if caps.check(c, user).allowed)),
            "node": NODE_ID}


@router.post("/app/login")
async def login(req: Login, request: Request):
    if (fwd := await route(request, req.model_dump())) is not None:
        return fwd
    expected = _PASSWORDS.get(req.user)
    given = hashlib.pbkdf2_hmac("sha256", req.password.encode(), _SALT, 100_000)
    ok = expected is not None and hmac.compare_digest(expected, given)
    audit.append("login", {"subject": req.user, "allowed": ok})
    await node.sense({"source": f"{req.user}@{client_ip(request)}", "actor": req.user, "path": "/login",
                      "decision": "allowed" if ok else "denied"})
    if not ok:
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
    return {"token": make_token(req.user), "profile": profile(req.user)}


@router.get("/app/me")
async def me(request: Request, authorization: str = Header("")):
    if (fwd := await route(request)) is not None:
        return fwd
    return profile(await session_user(authorization))


@router.get("/app/grades")
async def grades(request: Request, authorization: str = Header("")):
    if (fwd := await route(request)) is not None:
        return fwd
    user = await session_user(authorization)
    d = await decide(user, "read", client_ip(request))
    if not d["allowed"]:
        raise denied(d)
    return {"grades": book["grades"], "version": book["version"], "node": NODE_ID, "via": d["model"]}


@router.put("/app/grades/{student}")
async def set_grade(student: str, req: Score, request: Request, authorization: str = Header("")):
    if (fwd := await route(request, req.model_dump())) is not None:
        return fwd
    user = await session_user(authorization)
    if student not in book["grades"]:
        raise HTTPException(404, "Không có sinh viên này trong sổ")
    d = await decide(user, "write", client_ip(request), f"/grades-ds/{student}")
    if not d["allowed"]:
        raise denied(d)
    book["grades"][student] = round(req.score, 1)
    book["version"] += 1
    update = identity.signed({"student": student, "score": book["grades"][student],
                              "version": book["version"], "by": user, "node": NODE_ID})
    audit.append("grade_written", {"student": student, "score": book["grades"][student], "by": user})
    replies = await node.call_many(list(PEERS), "POST", "/peer/grade", update)
    return {"grades": book["grades"], "version": book["version"], "node": NODE_ID,
            "replicas": {n: "ok" if c == 200 else "không phản hồi" for n, (c, _) in replies.items()}}


@router.get("/app/shares")
async def shares(request: Request, authorization: str = Header("")):
    if (fwd := await route(request)) is not None:
        return fwd
    user = await session_user(authorization)
    live = [c for c in book["tickets"] if caps.check(c).allowed]
    view = lambda c: {k: c["payload"][k] for k in ("issuer", "subject", "actions", "expires", "may_delegate", "depth", "node")}
    return {"received": [view(c) for c in live if c["payload"]["subject"] == user],
            "given": [view(c) for c in live if c["payload"]["issuer"] == user], "node": NODE_ID}


@router.post("/app/shares")
async def share(req: Share, request: Request, authorization: str = Header("")):
    if (fwd := await route(request, req.model_dump())) is not None:
        return fwd
    user = await session_user(authorization)
    if req.to not in PROFILES or req.to == user:
        raise HTTPException(400, "Người nhận không hợp lệ")
    try:
        if all(evaluate(user, RESOURCE, a).allowed for a in req.actions):
            cap = caps.issue(user, req.to, RESOURCE, req.actions, req.minutes * 60, req.may_delegate)
        else:
            parent = next((c for c in book["tickets"] if c["payload"]["subject"] == user
                           and c["payload"]["may_delegate"] and caps.check(c, user).allowed), None)
            if parent is None:
                raise PermissionError("bạn không có quyền này để chia sẻ")
            cap = caps.delegate(parent, user, req.to, req.actions, req.minutes * 60, req.may_delegate)
    except PermissionError as exc:
        raise HTTPException(403, f"Không chia sẻ được: {exc}") from exc
    book["tickets"].append(cap)
    audit.append("share", {k: cap["payload"][k] for k in ("issuer", "subject", "actions", "depth")})
    await node.call_many(list(PEERS), "POST", "/peer/ticket", cap)
    return {"ok": True, "node": NODE_ID}


@router.get("/app/admin")
async def admin(request: Request, authorization: str = Header("")):
    if (fwd := await route(request)) is not None:
        return fwd
    user = await session_user(authorization)
    if SUBJECTS[user]["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị hệ thống xem được trang này")
    results = await node.call_many(node.nodes(), "GET", "/status")
    return {"node": NODE_ID, "nodes": [{"reachable": True, **data} if code == 200 else {"node_id": n, "reachable": False}
                                       for n, (code, data) in results.items()]}


class Drill(BaseModel):
    node: str = Field(max_length=32)


@router.post("/app/admin/tamper")
async def drill_tamper(req: Drill, authorization: str = Header("")):
    """Diễn tập: giả sử kẻ tấn công chiếm một node và sửa nhật ký mà không tính lại hash."""
    user = await session_user(authorization)
    if SUBJECTS[user]["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị hệ thống được diễn tập")
    if req.node != NODE_ID:
        if req.node not in PEERS:
            raise HTTPException(404, f"không có node {req.node}")
        code, data = await node.call(req.node, "POST", "/app/admin/tamper", json=req.model_dump(),
                                     headers={"authorization": authorization, "x-hop": "1"})
        if code is None:
            raise HTTPException(503, f"{req.node} không phản hồi")
        if code != 200:
            raise HTTPException(code, data.get("detail", f"{req.node} trả {code}"))
        return data
    records = audit.tail(500)
    if not records:
        raise HTTPException(404, f"{NODE_ID} chưa có bản ghi nào")
    target = next((r for r in reversed(records) if r["event"] in ("access", "login") and not r["data"].get("allowed")), records[-1])
    audit.tamper(target["index"])
    return {"node": NODE_ID, "index": target["index"], "event": target["event"], "verification": audit.verify()}


# ---------------- nhân bản giữa các node ----------------


@router.post("/peer/grade")
async def peer_grade(signed: dict):
    p = signed.get("payload") or {}
    origin = str(p.get("node", ""))
    await node.ensure_key(origin)
    key = keyring.key_of(origin)
    if key is None or not verify(key, p, str(signed.get("signature", ""))) or p.get("student") not in book["grades"]:
        audit.append("grade_rejected", {"claimed_node": origin, "student": p.get("student")})
        raise HTTPException(400, f"bản cập nhật không có chữ ký hợp lệ của node trong cluster ({origin})")
    # shortcut: ghi đồng thời ở 2 node thì bản đến sau thắng; cần vector clock nếu muốn gộp đúng.
    book["grades"][p["student"]] = p["score"]
    book["version"] = max(book["version"], int(p["version"]))
    audit.append("grade_replicated", {"student": p["student"], "score": p["score"], "from": origin})
    return {"node_id": NODE_ID, "version": book["version"]}


@router.post("/peer/ticket")
async def peer_ticket(cap: dict):
    await node.ensure_key(str((cap.get("payload") or {}).get("node", "")))
    d = caps.check(cap)
    if not d.allowed:
        audit.append("ticket_rejected", {"reason": d.reason})
        raise HTTPException(400, f"Từ chối quyền chia sẻ: {d.reason}")
    if cap not in book["tickets"]:
        book["tickets"].append(cap)
    return {"node_id": NODE_ID}
