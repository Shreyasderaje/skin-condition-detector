"""Analytics summary + trends over seeded consultations."""
from tests.conftest import give_consent, upload_image


def test_summary_counts(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    upload_image(client, auth_headers, patient_id)
    upload_image(client, auth_headers, patient_id)

    resp = client.get("/api/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total_consultations"] == 2
    assert sum(body["risk_distribution"].values()) == 2
    assert body["referral_rate"] == 0.0
    assert body["avg_response_time_hours"] is None
    assert sum(body["condition_breakdown"].values()) == 2


def test_summary_requires_auth(client):
    assert client.get("/api/analytics/summary").status_code == 401


def test_trends_periods(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    upload_image(client, auth_headers, patient_id)

    resp = client.get("/api/analytics/trends?period=7days", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["points"]) == 7
    assert sum(p["total"] for p in body["points"]) >= 1

    bad = client.get("/api/analytics/trends?period=2hours", headers=auth_headers)
    assert bad.status_code == 400
