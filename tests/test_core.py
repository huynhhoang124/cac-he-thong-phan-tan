import time

import pytest

from demo.audit import AuditChain
from demo.models import (
    AccessRequest,
    CapabilityDelegateRequest,
    CapabilityIssueRequest,
    Resource,
    SecurityEvent,
    Subject,
)
from demo.monitoring import CollaborativeDetector
from demo.policy import CapabilityService, PolicyEngine
from demo.security import NodeIdentity


@pytest.fixture()
def identity(tmp_path):
    return NodeIdentity("test-node", str(tmp_path))


@pytest.fixture()
def resource():
    return Resource(resource_id="grades", owner="registrar", classification="confidential", department="cs", course="ds")


@pytest.fixture()
def alice():
    return Subject(subject_id="alice", role="teacher", department="cs", courses=["ds"], clearance="confidential")


def test_abac_allows_teacher_for_matching_course(alice, resource):
    decision = PolicyEngine().evaluate(AccessRequest(subject=alice, resource=resource, action="read"))
    assert decision.allowed


def test_abac_denies_guest_by_default(resource):
    mallory = Subject(subject_id="mallory", role="guest")
    decision = PolicyEngine().evaluate(AccessRequest(subject=mallory, resource=resource, action="read"))
    assert not decision.allowed
    assert "clearance" in decision.reason


def test_capability_prevents_privilege_expansion(identity, alice, resource):
    service = CapabilityService(identity, PolicyEngine())
    parent = service.issue(CapabilityIssueRequest(issuer=alice, subject_id="bob", resource=resource, actions=["read"], may_delegate=True))
    assert service.verify(parent, subject="bob", resource="grades", action="read").allowed
    assert not service.verify(parent, subject="bob", resource="grades", action="write").allowed
    with pytest.raises(PermissionError, match="mở rộng"):
        service.delegate(CapabilityDelegateRequest(parent=parent, subject_id="carol", actions=["write"]))


def test_delegated_capability_is_attenuated(identity, alice, resource):
    service = CapabilityService(identity, PolicyEngine())
    parent = service.issue(CapabilityIssueRequest(issuer=alice, subject_id="bob", resource=resource, actions=["read", "write"], ttl_seconds=300, may_delegate=True))
    child = service.delegate(CapabilityDelegateRequest(parent=parent, subject_id="carol", actions=["read"], ttl_seconds=120))
    assert child["payload"]["actions"] == ["read"]
    assert child["payload"]["expires_at"] <= parent["payload"]["expires_at"]
    assert child["payload"]["depth"] == 1


def test_audit_chain_detects_tampering():
    chain = AuditChain("node-a")
    chain.append("one", {"value": 1})
    chain.append("two", {"value": 2})
    assert chain.verify()["valid"]
    assert chain.tamper_for_demo()
    assert not chain.verify()["valid"]


def test_detector_requires_two_reporters(identity):
    detector = CollaborativeDetector("node-a", identity, quorum=2)
    event = SecurityEvent(event_id="1", source="attacker", actor="mallory", action="read", resource="grades", decision="denied", ground_truth="malicious")
    detector.observe(event)
    detector.observe(event.model_copy(update={"event_id": "2"}))
    alerts = detector.observe(event.model_copy(update={"event_id": "3"}))
    assert alerts
    fp = alerts[0]["payload"]["fingerprint"]
    assert fp not in detector.incidents

    remote_identity = NodeIdentity("node-b", "/tmp")
    payload = {**alerts[0]["payload"], "reporter": "node-b", "timestamp": time.time()}
    signed = {"payload": payload, "signature": remote_identity.sign(payload), "public_key": remote_identity.public_key_b64}
    detector.accept_verified_alert(signed)
    assert detector.incidents[fp]["confirmed"]
