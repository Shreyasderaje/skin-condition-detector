"""Core screening endpoints: image upload + inference, consultation
history, image retrieval, referral and follow-up management."""
import os
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, g, request, send_file

from extensions import db, utcnow
from ml import inference as ml_inference
from models.consent import Consent
from models.consultation import Consultation
from models.patient import Patient
from utils.audit import log_action
from utils.auth import phc_scope_ids, require_auth
from utils.image_handler import image_file_path, save_image
from utils.responses import err, ok
from utils.validators import is_allowed_image, open_and_validate_image

consultations_bp = Blueprint("consultations", __name__)

ALLOWED_OUTCOMES = {"healed", "ongoing", "escalated"}
ALLOWED_URGENCY = {"Routine", "Urgent", "Emergency"}


def _get_scoped(consultation_id):
    consultation = db.session.get(Consultation, consultation_id)
    if consultation is None or consultation.phc_id not in phc_scope_ids(g.staff):
        return None
    return consultation


@consultations_bp.post("/consultations/upload")
@require_auth
def upload_consultation():
    patient_id = request.form.get("patient_id", type=int)
    if not patient_id:
        return err("patient_id is required", 400)
    file = request.files.get("image")
    if file is None or not file.filename:
        return err("image file is required (JPG/PNG)", 400)
    if not is_allowed_image(file.filename, file.mimetype):
        return err("Unsupported image format. Use JPG or PNG.", 400)

    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.phc_id not in phc_scope_ids(g.staff):
        return err("Patient not found", 404)

    consent = Consent.query.filter_by(
        patient_id=patient.id, consent_to_screening=True
    ).first()
    if consent is None:
        return err(
            "Patient consent for screening is required before upload "
            "(collect it on the intake form)",
            403,
        )

    vitals_temp = request.form.get("vitals_temp", type=float)
    if vitals_temp is not None and not 30.0 <= vitals_temp <= 45.0:
        return err("vitals_temp must be in °C between 30 and 45", 400)

    try:
        img = open_and_validate_image(file.stream)
    except ValueError as exc:
        return err(str(exc), 400)

    result = ml_inference.predict(img)  # <500ms with the real model
    filename = save_image(img, current_app.config["UPLOAD_FOLDER"])

    consultation = Consultation(
        patient_id=patient.id,
        phc_id=patient.phc_id,
        image_path=filename,
        model_mode=result["mode"],
        risk_level=result["risk_level"],
        confidence_scores=result["confidence"],
        condition_type=result["condition_type"],
        vitals_temp=vitals_temp,
    )
    db.session.add(consultation)
    db.session.flush()
    log_action(
        "upload_image",
        consultation.id,
        {"patient_id": patient.id, "risk_level": consultation.risk_level,
         "mode": consultation.model_mode},
    )
    db.session.commit()

    payload = {
        "consultation_id": consultation.id,
        "risk_level": consultation.risk_level,
        "confidence": consultation.confidence_scores,
        "condition_type": consultation.condition_type,
        "recommendation": result["recommendation"],
        "medical_disclaimer": result["medical_disclaimer"],
        "mode": result["mode"],
        "timestamp": consultation.created_at.isoformat(),
    }
    if "notice" in result:
        payload["notice"] = result["notice"]
    return ok(payload, 201)


@consultations_bp.get("/consultations")
@require_auth
def list_consultations():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    limit = min(max(request.args.get("limit", 20, type=int) or 20, 1), 100)
    query = Consultation.query.filter(
        Consultation.phc_id.in_(phc_scope_ids(g.staff))
    )

    patient_id = request.args.get("patient_id", type=int)
    if patient_id:
        query = query.filter(Consultation.patient_id == patient_id)
    risk_level = request.args.get("risk_level")
    if risk_level:
        query = query.filter(Consultation.risk_level == risk_level.upper())
    try:
        start = request.args.get("start_date")
        if start:
            query = query.filter(Consultation.created_at >= datetime.fromisoformat(start))
        end = request.args.get("end_date")
        if end:
            query = query.filter(
                Consultation.created_at < datetime.fromisoformat(end) + timedelta(days=1)
            )
    except ValueError:
        return err("Invalid date filter (use YYYY-MM-DD)", 400)

    pagination = (
        query.order_by(Consultation.created_at.desc())
        .paginate(page=page, per_page=limit, error_out=False)
    )
    return ok(
        {
            "items": [c.to_dict() for c in pagination.items],
            "page": pagination.page,
            "limit": limit,
            "total": pagination.total,
        }
    )


@consultations_bp.get("/consultations/<int:consultation_id>")
@require_auth
def get_consultation(consultation_id):
    consultation = _get_scoped(consultation_id)
    if consultation is None:
        return err("Consultation not found", 404)
    log_action("view_consultation", consultation.id)
    db.session.commit()
    return ok(consultation.to_dict(include_patient=True))


@consultations_bp.get("/consultations/<int:consultation_id>/image")
@require_auth
def get_image(consultation_id):
    consultation = _get_scoped(consultation_id)
    if consultation is None:
        return err("Consultation not found", 404)
    path = image_file_path(consultation.image_path, current_app.config["UPLOAD_FOLDER"])
    if not os.path.exists(path):
        return err("Image file missing", 404)
    log_action("view_image", consultation.id)
    db.session.commit()
    return send_file(path, mimetype="image/jpeg")


@consultations_bp.patch("/consultations/<int:consultation_id>/notes")
@require_auth
def update_notes(consultation_id):
    consultation = _get_scoped(consultation_id)
    if consultation is None:
        return err("Consultation not found", 404)
    data = request.get_json(silent=True) or {}
    if data.get("staff_notes") is None:
        return err("staff_notes is required", 400)
    consultation.staff_notes = data["staff_notes"].strip() or None
    log_action("add_notes", consultation.id)
    db.session.commit()
    return ok(consultation.to_dict(include_patient=True))


@consultations_bp.post("/consultations/<int:consultation_id>/referral")
@require_auth
def create_referral(consultation_id):
    consultation = _get_scoped(consultation_id)
    if consultation is None:
        return err("Consultation not found", 404)
    data = request.get_json(silent=True) or {}

    referred = bool(data.get("referred_to_specialist", True))
    reason = (data.get("referral_reason") or "").strip()
    urgency = data.get("referral_urgency") or "Routine"
    if urgency not in ALLOWED_URGENCY:
        return err("referral_urgency must be Routine, Urgent or Emergency", 400)
    if referred and not reason:
        return err("referral_reason is required when referring", 400)
    follow_up = data.get("follow_up_date")
    if follow_up:
        try:
            follow_up = date.fromisoformat(follow_up)
        except ValueError:
            return err("follow_up_date must be YYYY-MM-DD", 400)

    consultation.referred_to_specialist = referred
    consultation.referral_reason = reason or None
    consultation.referral_urgency = urgency
    consultation.referral_specialist = data.get("referral_specialist") or None
    consultation.follow_up_date = follow_up
    consultation.referred_at = utcnow()
    log_action("generate_referral", consultation.id, {"urgency": urgency})
    db.session.commit()
    return ok(
        {
            "referral_record_created": True,
            "referral_id": consultation.id,
            "consultation": consultation.to_dict(include_patient=True),
        },
        201,
    )


@consultations_bp.patch("/consultations/<int:consultation_id>/outcome")
@require_auth
def update_outcome(consultation_id):
    consultation = _get_scoped(consultation_id)
    if consultation is None:
        return err("Consultation not found", 404)
    data = request.get_json(silent=True) or {}
    outcome = data.get("outcome")
    if outcome not in ALLOWED_OUTCOMES:
        return err("outcome must be one of: healed, ongoing, escalated", 400)
    consultation.outcome = outcome
    log_action("update_outcome", consultation.id, {"outcome": outcome})
    db.session.commit()
    return ok(consultation.to_dict(include_patient=True))
