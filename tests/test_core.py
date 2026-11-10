import time

import pytest

from demo.authz import Capabilities, evaluate
from demo.crypto import Identity
from demo.monitor import Detector, Firewall
from demo.trust import AuditChain, Keyring


@pytest.fixture()
def node_a():
    ident = Identity("node-a")
    return ident, Keyring("node-a", ident.public_key)


def test_policy_models():
    cases = [("root", "grades-ds", "delete", "campus", True, "RBAC"),
             ("registrar", "grades-ds", "write", "campus", True, "DAC"),
             ("alice", "grades-ds", "read", "campus", True, "ABAC"),
             ("mallory", "grades-ds", "read", "public", False, "MAC"),
             ("alice", "exam-ds", "read", "public", False, "ABAC"),
             ("bob", "grades-ds", "write", "campus", False, "fail-safe")]
    for s, r, a, z, allowed, model in cases:
        d = evaluate(s, r, a, z)
        assert (d.allowed, d.model) == (allowed, model), (s, r, a, d)


def test_unknown_subject_is_denied():
    assert evaluate("eve", "grades-ds", "read").model == "fail-safe"


def test_capability_checked_by_other_node(node_a):
    ident_a, ring_a = node_a
    ident_b = Identity("node-b")
    ring_b = Keyring("node-b", ident_b.public_key)
    cap = Capabilities(ident_a, ring_a).issue("alice", "bob", "grades-ds", ["read"])
    b = Capabilities(ident_b, ring_b)
    assert "không thuộc cluster" in b.check(cap, "bob", "grades-ds", "read").reason
    ring_b.learn("node-a", ident_a.public_key)
    assert b.check(cap, "bob", "grades-ds", "read").allowed
    assert not b.check(cap, "bob", "grades-ds", "write").allowed


def test_forged_capability_rejected(node_a):
    ident_a, ring_a = node_a
    svc = Capabilities(ident_a, ring_a)
    cap = svc.issue("alice", "bob", "grades-ds", ["read"])
    forged = {**cap["payload"], "subject": "mallory", "actions": ["write"]}
    assert "chữ ký" in svc.check({"payload": forged, "signature": Identity("x").sign(forged)}).reason
    with pytest.raises(PermissionError):
        svc.issue("mallory", "mallory", "grades-ds", ["read"])


def test_keyring_pins_first_key():
    ring = Keyring("node-a", "k-a")
    assert ring.learn("node-b", "k-b")
    assert not ring.learn("node-b", "k-evil")
    assert ring.key_of("node-b") == "k-b"


def test_delegation_only_attenuates(node_a):
    svc = Capabilities(*node_a)
    bob = svc.issue("alice", "bob", "grades-ds", ["read", "write"], ttl=300, may_delegate=True)
    carol = svc.delegate(bob, "bob", "carol", ["read"], ttl=600)
    p = carol["payload"]
    assert p["actions"] == ["read"] and p["depth"] == 1 and p["parent"]
    assert p["expires"] <= bob["payload"]["expires"]
    with pytest.raises(PermissionError, match="mở rộng"):
        svc.delegate(bob, "bob", "carol", ["delete"])
    with pytest.raises(PermissionError, match="may_delegate"):
        svc.delegate(carol, "carol", "mallory", ["read"])
    with pytest.raises(PermissionError):
        svc.delegate(bob, "mallory", "carol", ["read"])  # không phải người giữ vé


def test_audit_chain_detects_tampering():
    chain = AuditChain("node-a")
    for i in range(3):
        chain.append("e", {"i": i})
    assert chain.verify()["valid"]
    chain.tamper(1)
    assert chain.verify() == {"valid": False, "broken_at": 1, "length": 3}


def _event(source, decision="denied", path="/"):
    return {"source": source, "actor": "x", "path": path, "decision": decision}


def test_detector_needs_quorum_and_rejects_forgery(node_a):
    ident_a, ring_a = node_a
    ident_b = Identity("node-b")
    ring_a.learn("node-b", ident_b.public_key)
    a = Detector(ident_a, ring_a)
    alerts = [x for _ in range(3) for x in a.observe(_event("1.2.3.4"))]
    assert len(alerts) == 1 and not a.incidents
    assert a.observe(_event("5.6.7.8", path="/../etc"))[0]["payload"]["kind"] == "SIDS"

    b = Detector(ident_b, Keyring("node-b", ident_b.public_key))
    report = [x for _ in range(3) for x in b.observe(_event("1.2.3.4"))][0]
    assert a.accept(report)["confirmed"]
    assert a.incidents["AIDS|1.2.3.4"]["reporters"] == ["node-a", "node-b"]

    fake_payload = {**report["payload"], "source": "9.9.9.9"}
    with pytest.raises(ValueError, match="chữ ký"):
        a.accept({"payload": fake_payload, "signature": Identity("f").sign(fake_payload)})
    with pytest.raises(ValueError, match="không thuộc cluster"):
        a.accept(Identity("node-z").signed({**fake_payload, "reporter": "node-z"}))


def test_detector_correlates_by_receive_time(node_a):
    ident_a, ring_a = node_a
    ident_b = Identity("node-b")
    ring_a.learn("node-b", ident_b.public_key)
    a = Detector(ident_a, ring_a, correlate=0.05)
    a.observe(_event("1.1.1.1")); a.observe(_event("1.1.1.1")); a.observe(_event("1.1.1.1"))
    time.sleep(0.1)
    late = ident_b.signed({"kind": "AIDS", "source": "1.1.1.1", "evidence": "", "actor": "x", "reporter": "node-b"})
    assert not a.accept(late)["confirmed"]


def test_firewall_limits_rate_and_size():
    fw = Firewall(limit=3)
    assert [fw.admit("ip", 10) for _ in range(4)][-1][0] == 429
    assert fw.admit("other", 10) is None
    assert fw.admit("other", 70_000)[0] == 413
