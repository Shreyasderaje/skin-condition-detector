"""Disclaimer (public) + consent recording."""


def test_disclaimer_public_no_auth(client):
    resp = client.get("/api/disclaimer")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "NOT a medical diagnosis" in body["disclaimer_text"]
    assert body["version"]


def test_consent_requires_patient(client, auth_headers):
    resp = client.post(
        "/api/consent",
        json={"patient_id": 9999, "consent_to_screening": True, "consent_to_data_storage": True},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_consent_requires_at_least_one_flag(client, auth_headers, patient_id):
    resp = client.post(
        "/api/consent",
        json={"patient_id": patient_id, "consent_to_screening": False, "consent_to_data_storage": False},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_consent_recorded(client, auth_headers, patient_id):
    resp = client.post(
        "/api/consent",
        json={"patient_id": patient_id, "consent_to_screening": True, "consent_to_data_storage": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()["consent_record_id"]
    assert resp.get_json()["consent_to_screening"] is True
