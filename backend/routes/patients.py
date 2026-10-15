"""Patient management endpoints (PHC-scoped)."""
from flask import Blueprint, g, request

from extensions import db
from models.patient import Patient
from utils.audit import log_action
from utils.auth import phc_scope_ids, require_auth
from utils.responses import err, ok
from utils.validators import validate_age, validate_gender, validate_phone

patients_bp = Blueprint("patients", __name__)


@patients_bp.post("/patients")
@require_auth
def create_patient():
    data = request.get_json(silent=True) or {}
    if data.get("age") is None or not data.get("gender") or not data.get("location"):
        return err("Fields age, gender and location are required", 400)
    try:
        age = int(data["age"])
    except (TypeError, ValueError):
        return err("age must be a number", 400)
    if not validate_age(age):
        return err("age must be between 1 and 120", 400)
    gender = data["gender"]
    if not validate_gender(gender):
        return err("gender must be Male, Female or Other", 400)
    contact = data.get("contact_number") or None
    if not validate_phone(contact):
        return err("contact_number must be in E.164 format, e.g. +919876543210", 400)

    patient = Patient(
        phc_id=g.staff.id,
        age=age,
        gender=gender,
        location=data["location"].strip(),
        contact_number=contact,
    )
    db.session.add(patient)
    db.session.flush()
    log_action("create_patient", patient.id)
    db.session.commit()
    return ok({"patient_id": patient.id, "created_at": patient.created_at.isoformat()}, 201)


@patients_bp.get("/patients")
@require_auth
def list_patients():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    limit = min(max(request.args.get("limit", 20, type=int) or 20, 1), 100)
    query = (
        Patient.query.filter(Patient.phc_id.in_(phc_scope_ids(g.staff)))
        .order_by(Patient.created_at.desc())
    )
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    return ok(
        {
            "items": [p.to_dict() for p in pagination.items],
            "page": pagination.page,
            "limit": limit,
            "total": pagination.total,
        }
    )


@patients_bp.get("/patients/<int:patient_id>")
@require_auth
def get_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.phc_id not in phc_scope_ids(g.staff):
        return err("Patient not found", 404)
    return ok(patient.to_dict())
