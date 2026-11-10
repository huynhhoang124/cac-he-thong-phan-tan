"""Một node đơn (không peer) qua TestClient: câu chuyện 4 màn phải chạy trọn vẹn."""
import pytest
from fastapi.testclient import TestClient

from demo.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset():
    client.post("/admin/reset")


def act(n):
    r = client.post(f"/demo/act/{n}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["steps"] and data["section"] and data["lesson"]
    return data


def decisions(data):
    """Trạng thái các bước quyết định truy cập (bỏ bước cảnh báo của sensor)."""
    return [s["status"] for s in data["steps"] if s.get("model") != "CIDS"]


def test_act1_reference_monitor_feeds_sensor():
    data = act(1)
    assert decisions(data) == ["allow", "deny", "deny", "deny"]
    alerts = [s for s in data["steps"] if s.get("model") == "CIDS"]
    assert len(alerts) == 1 and "AIDS 203.0.113.77" in alerts[0]["label"]


def test_act2_delegation_attenuates():
    data = act(2)
    assert decisions(data) == ["allow", "allow", "deny", "allow", "deny"]
    assert [p["depth"] for p in data["viz"]["chain"]] == [0, 1]


def test_act3_forged_tickets_rejected():
    act(1)
    act(2)
    data = act(3)
    reasons = [s["reason"] for s in data["steps"] if s["status"] == "deny"]
    assert any("vé cấp cho carol" in r for r in reasons)
    assert any("chữ ký không khớp" in r for r in reasons)
    assert any("không thuộc cluster" in r for r in reasons)
    assert "chưa thành incident" in data["steps"][-1]["label"]  # một node không đủ quorum


def test_act4_tamper_detected():
    act(1)
    data = act(4)
    assert data["viz"]["broken_at"] is not None
    assert client.get("/audit/verify").json()["valid"] is False


def test_acts_run_standalone_in_any_order():
    for n in (4, 3, 2, 1):
        act(n)
    assert client.post("/demo/act/5").status_code == 404


def test_claims_are_ignored():
    r = client.post("/access/check", json={"subject": "mallory", "resource": "grades-ds", "action": "read",
                                           "claims": {"role": "admin"}}).json()
    assert r["allowed"] is False and r["ignored_claims"] == {"role": "admin"}


def test_cluster_and_identity():
    assert client.get("/identity").json()["node_id"]
    nodes = client.get("/cluster").json()["nodes"]
    assert nodes[0]["reachable"] and nodes[0]["audit"]["valid"]
