"""Sổ điểm DS trên một node đơn: đăng nhập, phân quyền, chia sẻ, diễn tập nhật ký."""
import base64
import json

import pytest
from fastapi.testclient import TestClient

from sodiem import gradebook
from sodiem.main import app
from sodiem.node import audit, detector, identity

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset():
    gradebook.reset()
    audit.clear()
    detector.reset()


def login(user, password=None):
    r = client.post("/app/login", json={"user": user, "password": password or f"{user}123"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def test_wrong_password_rejected():
    assert client.post("/app/login", json={"user": "alice", "password": "x"}).status_code == 401


def test_teacher_reads_and_writes():
    h = login("alice")
    assert client.get("/app/grades", headers=h).json()["grades"]["bob"] == 7.5
    r = client.put("/app/grades/bob", json={"score": 9}, headers=h)
    assert r.status_code == 200 and r.json()["version"] == 1


def test_guest_blocked_by_mac_and_forged_session_rejected():
    h = login("mallory")
    r = client.get("/app/grades", headers=h)
    assert r.status_code == 403 and "MAC" in r.json()["detail"]
    signed = json.loads(base64.urlsafe_b64decode(h["Authorization"][7:]))
    signed["payload"]["user"] = "root"
    forged = "Bearer " + base64.urlsafe_b64encode(json.dumps(signed).encode()).decode()
    assert client.get("/app/grades", headers={"Authorization": forged}).status_code == 401


def test_share_chain_attenuates():
    a, b, c = login("alice"), login("bob"), login("carol")
    assert client.get("/app/grades", headers=b).status_code == 403
    assert client.post("/app/shares", headers=a, json={"to": "bob", "actions": ["read", "write"], "may_delegate": True}).status_code == 200
    assert client.get("/app/grades", headers=b).json()["via"] == "capability"
    r = client.post("/app/shares", headers=b, json={"to": "carol", "actions": ["read", "delete"]})
    assert r.status_code == 403 and "mở rộng" in r.json()["detail"]
    assert client.post("/app/shares", headers=b, json={"to": "carol", "actions": ["read"]}).status_code == 200
    assert client.get("/app/grades", headers=c).status_code == 200
    assert client.put("/app/grades/carol", headers=c, json={"score": 10}).status_code == 403


def test_repeated_denials_raise_local_alert():
    h = login("mallory")
    for _ in range(3):
        client.get("/app/grades", headers=h)
    assert any(a["kind"] == "AIDS" for a in detector.alerts)


def test_peer_grade_requires_valid_signature():
    good = identity.signed({"student": "bob", "score": 5.0, "version": 3, "by": "alice", "node": identity.node_id})
    forged = {**good, "payload": {**good["payload"], "score": 10.0}}
    assert client.post("/peer/grade", json=forged).status_code == 400
    assert client.post("/peer/grade", json=good).status_code == 200


def test_admin_only_and_tamper_drill_breaks_chain():
    assert client.get("/app/admin", headers=login("alice")).status_code == 403
    root = login("root")
    assert client.get("/app/admin", headers=root).json()["nodes"][0]["audit"]["valid"]
    r = client.post("/app/admin/tamper", headers=root, json={"node": identity.node_id})
    assert r.json()["verification"]["valid"] is False


def test_forged_hop_header_rejected_and_status_private():
    r = client.post("/app/login", json={"user": "mallory", "password": "x"}, headers={"x-hop": "1", "x-client": "1.2.3.4"})
    assert r.status_code == 401
    assert client.get("/status").status_code == 403
    assert client.get("/peer/state").status_code == 403
    from sodiem.node import hop_header
    assert client.get("/status", headers=hop_header()).status_code == 200


def test_replayed_old_update_cannot_roll_back():
    new = identity.signed({"student": "bob", "score": 9.0, "version": 2, "by": "alice", "node": identity.node_id})
    old = identity.signed({"student": "bob", "score": 1.0, "version": 1, "by": "alice", "node": identity.node_id})
    client.post("/peer/grade", json=new)
    assert client.post("/peer/grade", json=old).json()["ignored"] is True
    assert gradebook.book["grades"]["bob"] == 9.0


def test_cau4_modified_ticket_signature_mismatch():
    from sodiem.node import caps
    cap = caps.issue("alice", "carol", "grades-ds", ["read"], 600)
    stolen = {**cap, "payload": {**cap["payload"], "subject": "mallory", "actions": ["read", "write"]}}
    r = client.post("/peer/ticket", json=stolen)
    assert r.status_code == 400 and "chữ ký không khớp" in r.json()["detail"]


def test_cau4_presented_tickets_three_checks():
    a, c, m = login("alice"), login("carol"), login("mallory")
    client.post("/app/shares", headers=a, json={"to": "carol", "actions": ["read"]})
    cap = client.get("/app/shares", headers=c).json()["received"][0]["ticket"]
    assert client.post("/app/grades/ticket", headers=c, json={"ticket": cap}).status_code == 200
    stolen = client.post("/app/grades/ticket", headers=m, json={"ticket": cap})
    assert stolen.status_code == 403 and "không phải mallory" in stolen.json()["detail"]
    edited = {**cap, "payload": {**cap["payload"], "subject": "mallory"}}
    assert "chữ ký không khớp" in client.post("/app/grades/ticket", headers=m, json={"ticket": edited}).json()["detail"]
    forged = {**edited, "payload": {**edited["payload"], "node": "mallory-laptop"}}
    assert "không thuộc cluster" in client.post("/app/grades/ticket", headers=m, json={"ticket": forged}).json()["detail"]
    assert any(x["kind"] == "AIDS" and x["source"].startswith("mallory@") for x in detector.alerts)
