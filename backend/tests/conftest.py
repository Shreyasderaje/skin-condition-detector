"""Shared pytest fixtures. Each test gets a fresh SQLite file DB and
isolated upload folder. The demo model (no torch required) is used, so
the suite runs on requirements.txt alone."""
import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from extensions import db as _db  # noqa: E402

STAFF_A = {
    "staff_name": "Nurse Asha",
    "phc_name": "Mulki PHC",
    "email": "asha@mulki.in",
    "password": "password123",
}
STAFF_B = {
    "staff_name": "Nurse Vinod",
    "phc_name": "Kundapura PHC",
    "email": "vinod@kundapura.in",
    "password": "password456",
}


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            "RATE_LIMIT_PER_MINUTE": 1_000_000,
        }
    )
    yield application
    with application.app_context():
        _db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register(client, payload):
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201, resp.get_json()
    return {"Authorization": "Bearer " + resp.get_json()["access_token"]}


@pytest.fixture()
def auth_headers(client):
    return _register(client, STAFF_A)


@pytest.fixture()
def auth_headers_b(client):
    return _register(client, STAFF_B)


@pytest.fixture()
def patient_id(client, auth_headers):
    resp = client.post(
        "/api/patients",
        json={"age": 34, "gender": "Female", "location": "Mulki", "contact_number": "+919876543210"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["patient_id"]


def make_image_bytes(size=128, color=(190, 130, 100), fmt="PNG"):
    """Build a small synthetic in-memory image for upload tests."""
    img = Image.new("RGB", (size, size), color)
    buf = io.BytesIO()
    img.save(buf, fmt)
    buf.seek(0)
    return buf


def give_consent(client, headers, pid, screening=True, storage=True):
    resp = client.post(
        "/api/consent",
        json={"patient_id": pid, "consent_to_screening": screening, "consent_to_data_storage": storage},
        headers=headers,
    )
    assert resp.status_code == 201, resp.get_json()


def upload_image(client, headers, pid, buf=None, filename="lesion.png", mime="image/png"):
    buf = buf or make_image_bytes()
    return client.post(
        "/api/consultations/upload",
        data={"image": (buf, filename, mime), "patient_id": str(pid)},
        content_type="multipart/form-data",
        headers=headers,
    )
