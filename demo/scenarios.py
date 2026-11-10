"""Câu chuyện trình diễn: "Mallory muốn sửa bảng điểm", 4 màn.

Mỗi màn điều phối các node thật qua HTTP và trả về danh sách bước cho dashboard.
Các màn dùng chung trạng thái: vé của màn 2 được Mallory đánh cắp ở màn 3,
lần bị từ chối ở màn 1 là bản ghi Mallory muốn xóa ở màn 4.

status của một bước: allow (✓ được phép/đúng) · deny (✗ bị chặn) ·
alert (⚠ sensor/tấn công lộ ra) · info · down (node không phản hồi).
"""
from __future__ import annotations

import copy

from fastapi import APIRouter, HTTPException

from . import node
from .crypto import Identity
from .node import NODE_ID, PEERS, audit

router = APIRouter(prefix="/demo")

MALLORY_IP = "203.0.113.77"
ALICE_IP = "10.0.0.21"
story: dict = {}  # vé và chỉ số bản ghi truyền giữa các màn


def step(label: str, status: str, reason: str = "", *, node_id: str | None = None,
         src: str | None = None, model: str | None = None, detail: str | None = None) -> dict:
    return {k: v for k, v in {"label": label, "status": status, "reason": reason, "node": node_id,
                              "from": src, "model": model, "detail": detail}.items() if v is not None}


def down(n: str, data: dict) -> dict:
    return step(f"{n} không phản hồi", "down", data.get("detail", "partial failure"), node_id=n)


async def alive(candidates: list[str]) -> str:
    """Node còn sống đầu tiên trong danh sách ưu tiên; không còn ai thì dùng chính mình."""
    for n in candidates:
        if (await node.call(n, "GET", "/health"))[0] == 200:
            return n
    return NODE_ID


def sensor_steps(n: str, alerts: list[dict]) -> list[dict]:
    """Cảnh báo cục bộ do một lần truy cập sinh ra, và peer nhận được bao nhiêu reporter."""
    out = []
    for a in alerts:
        peers = [f"{p}: down" if r.get("down") else f"{p}: {len(r.get('reporters', []))} reporter"
                 + (" → INCIDENT" if r.get("confirmed") else "") for p, r in a["peers"].items()]
        out.append(step(f"Sensor {n}: {a['kind']} {a['source']}", "alert",
                        f"{a['evidence']} · ký và gửi peer — " + (", ".join(peers) or "không có peer"),
                        node_id=n, model="CIDS"))
    return out


async def access(at: str, who: str, action: str, label: str, *, resource: str = "grades-ds", zone: str = "campus",
                 cap: dict | None = None, claims: dict | None = None, source: str | None = None) -> list[dict]:
    """Một request tới node `at`. Trả về bước quyết định + bước cảnh báo (nếu có)."""
    code, d = await node.call(at, "POST", "/access/check", {
        "subject": who, "resource": resource, "action": action, "zone": zone,
        "capability": cap, "claims": claims, "source": source or (MALLORY_IP if who == "mallory" else ALICE_IP)},
        timeout=node.TIMEOUT * 3)  # node `at` có thể còn phải chuyển cảnh báo cho peer đã chết
    if code is None:
        return [down(at, d)]
    reason = d.get("reason", d.get("detail", ""))
    if claims:
        reason = f"thuộc tính tự khai {claims} bị bỏ qua, tra directory → {reason}"
    return [step(label, "allow" if d.get("allowed") else "deny", reason,
                 node_id=at, src=who, model=d.get("model"))] + sensor_steps(at, d.get("alerts", []))


def cap_detail(cap: dict) -> str:
    p = cap["payload"]
    parent = f" · parent {p['parent']}" if p.get("parent") else ""
    return f"{p['issuer']}→{p['subject']} {p['actions']} · depth {p['depth']} · ký bởi {p['node']}{parent} · sig {cap['signature'][:12]}…"


def result(act: int, title: str, section: str, lesson: str, steps: list[dict], **extra) -> dict:
    return {"act": act, "title": title, "section": section, "lesson": lesson, "steps": steps, **extra}


# ---------------- Màn 1: reference monitor ----------------

async def act1() -> dict:
    a = NODE_ID
    steps = []
    steps += await access(a, "alice", "read", "Alice (GV môn DS) đọc bảng điểm ở campus")
    steps += await access(a, "mallory", "read", "Mallory (guest) đọc bảng điểm")
    steps += await access(a, "mallory", "read", "Mallory tự khai role=admin", claims={"role": "admin"})
    steps += await access(a, "mallory", "write", "Mallory thử sửa bảng điểm")
    return result(1, "Ai được đọc bảng điểm?", "9.5.1 – 9.5.2",
                  "Một reference monitor, nhiều mô hình (ABAC, MAC), mặc định từ chối. Thuộc tính lấy từ directory, "
                  "không tin client tự khai. Mỗi lần từ chối cũng là dữ liệu cho sensor — nhưng một node nghi ngờ chưa thành incident.",
                  steps)


# ---------------- Màn 2: capability + delegation xuyên node ----------------

async def act2() -> dict:
    peers = list(PEERS)
    b = await alive(peers)                     # node-b, hoặc node khác nếu B đã chết
    c = await alive(list(reversed(peers)))     # node-c, hoặc node khác nếu C đã chết
    steps = []
    if peers and b != peers[0]:
        steps.append(step(f"{peers[0]} không phản hồi → Bob dùng {b}", "down", "partial failure: chọn node khác", node_id=peers[0]))

    code, bob = await node.call(NODE_ID, "POST", "/capabilities/issue", {
        "issuer": "alice", "subject": "bob", "resource": "grades-ds", "actions": ["read", "write"],
        "ttl": 600, "may_delegate": True})
    if code != 200:
        raise HTTPException(500, bob.get("detail", "không cấp được vé"))
    steps.append(step("Alice cấp vé cho Bob: [read, write], được ủy tiếp", "allow", "Alice có quyền nên được cấp lại",
                      node_id=NODE_ID, src="alice", detail=cap_detail(bob)))

    async def deleg(actions: list[str], label: str):
        code, d = await node.call(b, "POST", "/capabilities/delegate", {
            "parent": bob, "holder": "bob", "subject": "carol", "actions": actions, "ttl": 300})
        if code is None:
            steps.append(down(b, d))
            return None
        ok = code == 200
        steps.append(step(label, "allow" if ok else "deny",
                          f"{b} tự kiểm vé của {NODE_ID}, không hỏi lại · " + ("quyền con ⊆ quyền cha, hạn con ≤ hạn cha" if ok else d.get("detail", "")),
                          node_id=b, src="bob", detail=cap_detail(d) if ok else None))
        return d if ok else None

    carol = await deleg(["read"], "Bob ủy cho Carol [read]")
    await deleg(["read", "delete"], "Bob ủy cho Carol [read, delete]")
    story.update(bob=bob, carol=carol)
    if carol:
        steps += await access(c, "carol", "read", f"Carol đọc bảng điểm ở {c} bằng vé ủy quyền", cap=carol)
        steps += await access(c, "carol", "write", f"Carol thử ghi ở {c}", cap=carol)
    return result(2, "Ủy quyền đi qua ba node", "9.5.1 · 9.5.3",
                  "Vé có chữ ký nên node nào trong cluster cũng tự kiểm tại chỗ, không cần hỏi lại node cấp. "
                  "Ủy quyền chỉ giữ nguyên hoặc thu hẹp; chuỗi parent-hash giống attestation của WAVE.",
                  steps, viz={"type": "delegation", "chain": [x["payload"] for x in (bob, carol) if x]})


# ---------------- Màn 3: giả vé + collaborative IDS ----------------

async def act3() -> dict:
    if not story.get("carol"):
        await act2()
    carol = story["carol"]
    peers = list(PEERS)
    c = await alive(list(reversed(peers)))
    b = await alive([p for p in peers if p != c])
    steps = []

    stolen = carol
    forged = copy.deepcopy(carol["payload"])
    forged.update(subject="mallory", actions=["read", "write"])
    laptop = Identity("mallory-laptop")
    own = {**forged, "node": "mallory-laptop"}
    steps += await access(c, "mallory", "write", f"Mallory dùng lại vé đánh cắp của Carol ở {c}", cap=stolen)
    steps += await access(c, "mallory", "write", f"Mallory sửa vé thành của mình, ký giả {forged['node']}",
                          cap={"payload": forged, "signature": laptop.sign(forged)})
    steps += await access(c, "mallory", "write", "Mallory tự phát vé bằng khóa riêng",
                          cap={"payload": own, "signature": laptop.sign(own)})
    if b != c:
        steps += await access(b, "mallory", "write", f"Mallory thử ghi ở {b}")
        steps += await access(b, "mallory", "read", f"Mallory dò file hệ thống ở {b}", resource="../../etc/passwd")
        steps += await access(b, "mallory", "write", f"Mallory thử ghi ở {b} lần nữa")

    confirmed = {}
    for n, (code, data) in (await node.call_many(node.nodes(), "GET", "/status")).items():
        for inc in data.get("incidents", []) if code == 200 else []:
            if inc["source"] == MALLORY_IP:
                confirmed[n] = inc["reporters"]
    if confirmed:
        reporters = sorted({r for rs in confirmed.values() for r in rs})
        steps.append(step(f"INCIDENT {MALLORY_IP}: {len(reporters)} node độc lập cùng báo", "allow",
                          f"reporters: {', '.join(reporters)} · quorum 2 · ghép theo thời điểm nhận, không cần đồng hồ chung",
                          model="CIDS"))
    else:
        steps.append(step(f"{MALLORY_IP} chưa thành incident", "deny", "chưa đủ 2 node độc lập cùng báo", model="CIDS"))
    return result(3, "Mallory đổi chiến thuật", "9.4 · 9.6.2 – 9.6.3",
                  "Chữ ký chỉ có giá trị khi khóa thuộc cluster (trust anchor). Từng node chỉ thấy một phần; "
                  "khi nhiều node độc lập cùng báo, cảnh báo mới thành incident.",
                  steps)


# ---------------- Màn 4: xóa dấu vết ----------------

async def act4() -> dict:
    record = next((r for r in reversed(audit.tail(200)) if r["event"] == "access"
                   and r["data"].get("subject") == "mallory" and not r["data"].get("allowed")), None)
    if record is None:
        await access(NODE_ID, "mallory", "write", "")
        record = next(r for r in reversed(audit.tail(200)) if r["event"] == "access")
    i = record["index"]
    before = audit.verify()
    steps = [
        step(f"{NODE_ID} giữ bản ghi #{i}: mallory {record['data']['action']} grades-ds → bị từ chối", "deny",
             f"chuỗi hợp lệ, {before['length']} bản ghi, head {before['head'][:12]}…", node_id=NODE_ID),
    ]
    audit.tamper(i)
    after = audit.verify()
    steps += [
        step(f"Mallory chiếm {NODE_ID}, sửa #{i}: allowed false → true", "alert", "không tính lại hash", node_id=NODE_ID, src="mallory"),
        step(f"{NODE_ID} kiểm chuỗi: đứt tại #{after['broken_at']}", "deny",
             "hash không còn khớp nội dung → việc sửa bị lộ", node_id=NODE_ID),
    ]
    for n, (code, data) in (await node.call_many(list(PEERS), "GET", "/status")).items():
        if code is None:
            steps.append(down(n, data))
            continue
        inc = [x for x in data["incidents"] if x["source"] == MALLORY_IP]
        steps.append(step(f"{n} vẫn giữ bằng chứng riêng", "allow",
                          f"chuỗi {'hợp lệ' if data['audit']['valid'] else 'ĐỨT'}, {data['audit']['length']} bản ghi · "
                          + (f"incident {MALLORY_IP} ({', '.join(inc[0]['reporters'])})" if inc else "không có incident"),
                          node_id=n))
    return result(4, "Xóa dấu vết", "9.4.3",
                  "Hash chain không ngăn được việc sửa, nó làm việc sửa bị lộ. Bằng chứng nằm trên nhiều node, "
                  "nên chiếm một node không xóa được hết (ý tưởng nhân bản sổ cái của blockchain).",
                  steps, viz={"type": "chain", "records": audit.tail(6), "broken_at": after["broken_at"]})


ACTS = {1: act1, 2: act2, 3: act3, 4: act4}


@router.post("/act/{n}")
async def run_act(n: int):
    if n not in ACTS:
        raise HTTPException(404, "chỉ có màn 1–4")
    return await ACTS[n]()


def reset() -> None:
    story.clear()
