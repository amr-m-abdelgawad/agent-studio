from tests.unit.conftest import login


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_bootstrap_owner_can_login(client):
    me = login(client, "owner@test.com", "owner-password-12")
    assert me["email"] == "owner@test.com"
    assert me["org"]["name"] == "Test Org"
    assert me["org_role"] == "owner"
