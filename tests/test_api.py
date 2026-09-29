from fastapi.testclient import TestClient

from demo.main import app, audit


client = TestClient(app)


def setup_function():
    audit.clear()


def test_health_and_authorization_scenario():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    response = client.post("/demo/authorization", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["abac"]["alice_read"]["allowed"] is True
    assert data["abac"]["mallory_read"]["allowed"] is False
    assert data["delegation"]["bob_read"]["allowed"] is True
    assert data["delegation"]["bob_write"]["allowed"] is False


def test_sybil_scenario_compares_admission_modes():
    response = client.post("/demo/sybil", json={"count": 8, "stake_per_identity": 0})
    assert response.status_code == 200
    data = response.json()
    assert len(data["naive_accepted"]) == 8
    assert data["resistant_accepted"] == []


def test_audit_tamper_endpoint_exposes_integrity_failure():
    client.post("/demo/sybil", json={"count": 2, "stake_per_identity": 0})
    before = client.get("/audit").json()["verification"]
    assert before["valid"] is True
    after = client.post("/audit/tamper-demo", json={}).json()["verification"]
    assert after["valid"] is False


def test_local_cids_scenario_emits_alerts():
    response = client.post("/demo/cids", json={})
    assert response.status_code == 200
    snapshot = response.json()["local_snapshot"]
    assert snapshot["alerts"]
