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
