"""Patient CRUD + PHC isolation (403/404 scoping)."""


def test_create_and_get_patient(client, auth_headers):
    resp = client.post(
        "/api/patients",
        json={"age": 45, "gender": "Male", "location": "Mulki", "contact_number": "+919876543210"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    pid = resp.get_json()["patient_id"]

    got = client.get(f"/api/patients/{pid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.get_json()["age"] == 45
    assert got.get_json()["location"] == "Mulki"


def test_create_patient_validations(client, auth_headers):
    bad_age = client.post("/api/patients", json={"age": 300, "gender": "Male", "location": "Mulki"}, headers=auth_headers)
    assert bad_age.status_code == 400
    bad_gender = client.post("/api/patients", json={"age": 30, "gender": "Alien", "location": "Mulki"}, headers=auth_headers)
    assert bad_gender.status_code == 400
    bad_phone = client.post("/api/patients", json={"age": 30, "gender": "Male", "location": "Mulki", "contact_number": "123"}, headers=auth_headers)
    assert bad_phone.status_code == 400


def test_patient_list_paginates(client, auth_headers):
    for i in range(5):
        client.post("/api/patients", json={"age": 20 + i, "gender": "Other", "location": "Mulki"}, headers=auth_headers)
    resp = client.get("/api/patients?page=1&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 5


def test_patient_isolated_between_phcs(client, auth_headers, auth_headers_b):
    resp = client.post(
        "/api/patients", json={"age": 60, "gender": "Female", "location": "Mulki"}, headers=auth_headers
    )
    pid = resp.get_json()["patient_id"]

    other_phc = client.get(f"/api/patients/{pid}", headers=auth_headers_b)
    assert other_phc.status_code == 404  # must not leak existence across PHCs

    same_phc_colleague = client.post(
        "/api/auth/register",
        json={"staff_name": "Nurse Asha 2", "phc_name": "Mulki PHC", "email": "asha2@mulki.in", "password": "password789"},
    )
    headers = {"Authorization": "Bearer " + same_phc_colleague.get_json()["access_token"]}
    assert client.get(f"/api/patients/{pid}", headers=headers).status_code == 200
