from __future__ import annotations

import time
from dataclasses import dataclass

from .models import AccessRequest, CapabilityDelegateRequest, CapabilityIssueRequest
from .security import NodeIdentity, canonical_json, sha256_hex


CLASSIFICATION_LEVEL = {"public": 0, "confidential": 1, "restricted": 2}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


class PolicyEngine:
    def evaluate(self, request: AccessRequest) -> Decision:
        subject = request.subject
        resource = request.resource
        env = request.environment

        if subject.role == "admin":
            return Decision(True, "RBAC: admin có toàn quyền trong demo")
        if subject.subject_id == resource.owner:
            return Decision(True, "DAC: chủ sở hữu được phép truy cập")
        if request.action == "read" and resource.classification == "public":
            return Decision(True, "ABAC: tài nguyên public cho phép đọc")
        if env.network_zone == "public" and resource.classification == "restricted":
            return Decision(False, "ABAC: tài nguyên restricted yêu cầu campus hoặc VPN")
        if CLASSIFICATION_LEVEL[subject.clearance] < CLASSIFICATION_LEVEL[resource.classification]:
            return Decision(False, "ABAC: clearance thấp hơn classification")
        if subject.department != resource.department:
            return Decision(False, "ABAC: khác department")
        if subject.role == "teacher" and resource.course in subject.courses and request.action in {"read", "write"}:
            return Decision(True, "ABAC: teacher đúng course được đọc/ghi")
        return Decision(False, "Fail-safe default: không có luật cho phép phù hợp")


class CapabilityService:
    def __init__(self, identity: NodeIdentity, policy: PolicyEngine) -> None:
        self.identity = identity
        self.policy = policy

    def issue(self, request: CapabilityIssueRequest) -> dict:
        for action in request.actions:
            decision = self.policy.evaluate(
                AccessRequest(subject=request.issuer, resource=request.resource, action=action)
            )
            if not decision.allowed:
                raise PermissionError(f"Issuer không có quyền {action}: {decision.reason}")

        now = int(time.time())
        payload = {
            "version": 1,
            "issued_by_node": self.identity.node_id,
            "issuer": request.issuer.subject_id,
            "subject": request.subject_id,
            "resource": request.resource.resource_id,
            "actions": sorted(set(request.actions)),
            "issued_at": now,
            "expires_at": now + request.ttl_seconds,
            "may_delegate": request.may_delegate,
            "depth": 0,
            "parent_hash": None,
        }
        return {"payload": payload, "signature": self.identity.sign(payload), "public_key": self.identity.public_key_b64}

    def verify(self, capability: dict, *, subject: str | None = None, resource: str | None = None, action: str | None = None) -> Decision:
        try:
            payload = capability["payload"]
            valid_signature = NodeIdentity.verify(capability["public_key"], payload, capability["signature"])
        except (KeyError, TypeError):
            return Decision(False, "Capability không đúng cấu trúc")
        if not valid_signature:
            return Decision(False, "Chữ ký capability không hợp lệ")
        if int(payload.get("expires_at", 0)) < int(time.time()):
            return Decision(False, "Capability đã hết hạn")
        if subject is not None and payload.get("subject") != subject:
            return Decision(False, "Capability không thuộc subject")
        if resource is not None and payload.get("resource") != resource:
            return Decision(False, "Capability không áp dụng cho resource")
        if action is not None and action not in payload.get("actions", []):
            return Decision(False, "Capability không chứa action yêu cầu")
        return Decision(True, "Capability hợp lệ")

    def delegate(self, request: CapabilityDelegateRequest) -> dict:
        verified = self.verify(request.parent)
        if not verified.allowed:
            raise PermissionError(verified.reason)
        parent = request.parent["payload"]
        if not parent.get("may_delegate"):
            raise PermissionError("Capability cha không cho phép ủy quyền tiếp")
        if not set(request.actions).issubset(set(parent["actions"])):
            raise PermissionError("Không được mở rộng action khi ủy quyền")

        now = int(time.time())
        expires_at = min(now + request.ttl_seconds, int(parent["expires_at"]))
        payload = {
            "version": 1,
            "issued_by_node": self.identity.node_id,
            "issuer": parent["subject"],
            "subject": request.subject_id,
            "resource": parent["resource"],
            "actions": sorted(set(request.actions)),
            "issued_at": now,
            "expires_at": expires_at,
            "may_delegate": request.may_delegate,
            "depth": int(parent.get("depth", 0)) + 1,
            "parent_hash": sha256_hex(canonical_json(request.parent)),
        }
        return {"payload": payload, "signature": self.identity.sign(payload), "public_key": self.identity.public_key_b64}
