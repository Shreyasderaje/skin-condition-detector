"""Upload + inference + referral flow (demo model)."""
from tests.conftest import (
    give_consent,
    make_image_bytes,
    upload_image,
)


def test_upload_requires_consent(client, auth_headers, patient_id):
    resp = upload_image(client, auth_headers, patient_id)
    assert resp.status_code == 403
    assert "consent" in resp.get_json()["error"].lower()


def test_upload_end_to_end(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    resp = upload_image(client, auth_headers, patient_id)
    assert resp.status_code == 201, resp.get_json()
    body = resp.get_json()
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert abs(sum(body["confidence"].values()) - 1.0) < 0.01
    assert body["condition_type"]
    assert body["mode"] == "demo"  # no trained weights in the test env
    assert "NOT a diagnosis" in body["medical_disclaimer"]

    cid = body["consultation_id"]
    got = client.get(f"/api/consultations/{cid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.get_json()["patient"]["patient_id"] == patient_id


def test_upload_validations(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)

    bad_ext = upload_image(client, auth_headers, patient_id, filename="x.gif", mime="image/gif")
    assert bad_ext.status_code == 400

    tiny = upload_image(client, auth_headers, patient_id, buf=make_image_bytes(size=10))
    assert tiny.status_code == 400

    missing = client.post(
        "/api/consultations/upload",
        data={"patient_id": str(patient_id)},
        content_type="multipart/form-data",
        headers=auth_headers,
    )
    assert missing.status_code == 400


def test_image_endpoint_returns_bytes(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    cid = upload_image(client, auth_headers, patient_id).get_json()["consultation_id"]
    resp = client.get(f"/api/consultations/{cid}/image", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.data.startswith(b"\xff\xd8")  # JPEG magic bytes


def test_consultation_isolated_between_phcs(client, auth_headers, auth_headers_b, patient_id):
    give_consent(client, auth_headers, patient_id)
    cid = upload_image(client, auth_headers, patient_id).get_json()["consultation_id"]
    assert client.get(f"/api/consultations/{cid}", headers=auth_headers_b).status_code == 404
    assert client.get(f"/api/consultations/{cid}/image", headers=auth_headers_b).status_code == 404


def test_referral_and_outcome_flow(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    cid = upload_image(client, auth_headers, patient_id).get_json()["consultation_id"]

    no_reason = client.post(
        f"/api/consultations/{cid}/referral", json={}, headers=auth_headers
    )
    assert no_reason.status_code == 400

    resp = client.post(
        f"/api/consultations/{cid}/referral",
        json={
            "referred_to_specialist": True,
            "referral_reason": "Suspected malignancy",
            "referral_urgency": "Urgent",
            "referral_specialist": "Dermatologist",
            "follow_up_date": "2026-11-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.get_json()["consultation"]
    assert body["referred_to_specialist"] is True
    assert body["follow_up_date"] == "2026-11-01"

    outcome = client.patch(
        f"/api/consultations/{cid}/outcome", json={"outcome": "escalated"}, headers=auth_headers
    )
    assert outcome.status_code == 200
    assert outcome.get_json()["outcome"] == "escalated"

    bad_outcome = client.patch(
        f"/api/consultations/{cid}/outcome", json={"outcome": "unknown"}, headers=auth_headers
    )
    assert bad_outcome.status_code == 400


def test_notes_update(client, auth_headers, patient_id):
    give_consent(client, auth_headers, patient_id)
    cid = upload_image(client, auth_headers, patient_id).get_json()["consultation_id"]
    resp = client.patch(
        f"/api/consultations/{cid}/notes", json={"staff_notes": "Patient reports itching"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.get_json()["staff_notes"] == "Patient reports itching"
