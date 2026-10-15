"""Auth endpoint behaviour: register, login, token enforcement."""
from tests.conftest import STAFF_A


def test_register_returns_token(client):
    resp = client.post("/api/auth/register", json=STAFF_A)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["access_token"]
    assert body["staff_id"].startswith("STF-")
    assert body["staff"]["phc_name"] == "Mulki PHC"


def test_register_duplicate_email_conflict(client):
    client.post("/api/auth/register", json=STAFF_A)
    resp = client.post("/api/auth/register", json=STAFF_A)
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post("/api/auth/register", json={**STAFF_A, "password": "short"})
    assert resp.status_code == 400


def test_register_missing_field(client):
    resp = client.post("/api/auth/register", json={"email": "x@y.in"})
    assert resp.status_code == 400


def test_login_success_and_failure(client):
    client.post("/api/auth/register", json=STAFF_A)
    ok = client.post("/api/auth/login", json={"email": STAFF_A["email"], "password": STAFF_A["password"]})
    assert ok.status_code == 200
    assert ok.get_json()["phc_name"] == "Mulki PHC"

    bad = client.post("/api/auth/login", json={"email": STAFF_A["email"], "password": "wrong-pass"})
    assert bad.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/patients")
    assert resp.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    resp = client.get("/api/patients", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_logout(client, auth_headers):
    resp = client.post("/api/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
