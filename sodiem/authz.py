"""9.5 Authorization: reference monitor (RBAC/DAC/MAC/ABAC), capability, delegation."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from .crypto import Identity, canonical, sha256, verify
from .trust import Keyring

LEVEL = {"public": 0, "confidential": 1, "restricted": 2}
ACTIONS = ("read", "write", "delete")

# Attribute directory phía server (giống nhau trên mọi node vì cùng image).
# Thuộc tính client tự khai không bao giờ được dùng thay cho bảng này.
SUBJECTS = {
    "root":      {"role": "admin",   "department": "it", "courses": [],     "clearance": "restricted"},
    "registrar": {"role": "staff",   "department": "cs", "courses": [],     "clearance": "restricted"},
    "alice":     {"role": "teacher", "department": "cs", "courses": ["ds"], "clearance": "restricted"},
    "bob":       {"role": "student", "department": "cs", "courses": ["ds"], "clearance": "confidential"},
    "carol":     {"role": "student", "department": "cs", "courses": ["ds"], "clearance": "confidential"},
    "mallory":   {"role": "guest",   "department": "public", "courses": [], "clearance": "public"},
}
RESOURCES = {
    "grades-ds":   {"owner": "registrar", "classification": "confidential", "department": "cs", "course": "ds"},
    "exam-ds":     {"owner": "registrar", "classification": "restricted",   "department": "cs", "course": "ds"},
    "syllabus-ds": {"owner": "alice",     "classification": "public",       "department": "cs", "course": "ds"},
}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    model: str
    reason: str

    def dict(self) -> dict:
        return asdict(self)


def evaluate(subject_id: str, resource_id: str, action: str, zone: str = "campus") -> Decision:
    """Reference monitor: duyệt luật theo thứ tự, không khớp luật nào thì từ chối."""
    s, r = SUBJECTS.get(subject_id), RESOURCES.get(resource_id)
    if s is None or r is None:
        return Decision(False, "fail-safe", "subject hoặc resource không có trong directory")
    if s["role"] == "admin":
        return Decision(True, "RBAC", "vai trò admin được mọi thao tác")
    if subject_id == r["owner"]:
        return Decision(True, "DAC", f"{subject_id} là chủ sở hữu {resource_id}")
    if LEVEL[s["clearance"]] < LEVEL[r["classification"]]:
        return Decision(False, "MAC", f"nhãn {s['clearance']} < {r['classification']}")
    if r["classification"] == "public" and action == "read":
        return Decision(True, "ABAC", "tài nguyên public cho phép đọc")
    if r["classification"] == "restricted" and zone == "public":
        return Decision(False, "ABAC", "restricted chỉ truy cập từ campus/VPN, đang ở mạng public")
    if (s["role"] == "teacher" and s["department"] == r["department"]
            and r["course"] in s["courses"] and action in ("read", "write")):
        return Decision(True, "ABAC", f"teacher {s['department']}, dạy {r['course']}, zone {zone}")
    return Decision(False, "fail-safe", "không luật nào cho phép → mặc định từ chối")


class Capabilities:
    """Vé (capability) ký bởi node. Node nào trong cluster cũng tự kiểm được,
    không cần hỏi lại node phát vé, nhưng chỉ tin chữ ký của khóa trong keyring."""

    def __init__(self, identity: Identity, keyring: Keyring) -> None:
        self.identity = identity
        self.keyring = keyring

    def _sign(self, body: dict) -> dict:
        return self.identity.signed({**body, "node": self.identity.node_id})

    def issue(self, issuer: str, subject: str, resource: str, actions: list[str],
              ttl: int = 300, may_delegate: bool = False) -> dict:
        for action in actions:
            d = evaluate(issuer, resource, action)
            if not d.allowed:
                raise PermissionError(f"{issuer} không có quyền {action} để cấp: {d.reason}")
        now = int(time.time())
        return self._sign({"issuer": issuer, "subject": subject, "resource": resource,
                           "actions": sorted(set(actions)), "expires": now + ttl,
                           "may_delegate": may_delegate, "depth": 0, "parent": None})

    def check(self, cap: dict, subject: str | None = None, resource: str | None = None,
              action: str | None = None) -> Decision:
        try:
            p, sig = cap["payload"], cap["signature"]
            node = p["node"]
        except (KeyError, TypeError):
            return Decision(False, "capability", "vé sai cấu trúc")
        key = self.keyring.key_of(node)
        if key is None:
            return Decision(False, "capability", f"khóa ký '{node}' không thuộc cluster")
        if not verify(key, p, sig):
            return Decision(False, "capability", f"chữ ký không khớp khóa của {node}")
        if p["expires"] < time.time():
            return Decision(False, "capability", "vé đã hết hạn")
        if subject is not None and p["subject"] != subject:
            return Decision(False, "capability", f"vé cấp cho {p['subject']}, không phải {subject}")
        if resource is not None and p["resource"] != resource:
            return Decision(False, "capability", "vé không áp dụng cho resource này")
        if action is not None and action not in p["actions"]:
            return Decision(False, "capability", f"vé chỉ có {p['actions']}, không có {action}")
        return Decision(True, "capability", f"vé do {node} ký, {p['issuer']} → {p['subject']} {p['actions']}")

    def delegate(self, parent: dict, holder: str, subject: str, actions: list[str],
                 ttl: int = 120, may_delegate: bool = False) -> dict:
        """Attenuation: quyền con ⊆ quyền cha, hạn con ≤ hạn cha."""
        d = self.check(parent, subject=holder)
        if not d.allowed:
            raise PermissionError(d.reason)
        p = parent["payload"]
        if not p["may_delegate"]:
            raise PermissionError("vé cha không cho phép ủy quyền tiếp (may_delegate = false)")
        extra = set(actions) - set(p["actions"])
        if extra:
            raise PermissionError(f"không được mở rộng quyền: {sorted(extra)} không có trong vé cha")
        return self._sign({"issuer": holder, "subject": subject, "resource": p["resource"],
                           "actions": sorted(set(actions)), "expires": min(int(time.time()) + ttl, p["expires"]),
                           "may_delegate": may_delegate, "depth": p["depth"] + 1,
                           "parent": sha256(canonical(parent))[:16]})
