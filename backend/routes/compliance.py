"""Medical disclaimer + patient consent endpoints."""
from flask import Blueprint, g, request

from extensions import db
from models.consent import Consent
from models.patient import Patient
from utils.audit import log_action
from utils.auth import phc_scope_ids, require_auth
from utils.responses import err, ok

compliance_bp = Blueprint("compliance", __name__)

DISCLAIMER_TEXT = (
    "MEDICAL DISCLAIMER - READ BEFORE USE\n\n"
    "This tool is an AI-based screening aid for early triage of skin "
    "conditions at Primary Health Centers. It is NOT a medical diagnosis "
    "device and does not replace clinical judgement.\n\n"
    "- Results are probabilistic screening suggestions, not diagnoses.\n"
    "- All HIGH risk results must be followed by an in-person dermatologist "
    "referral.\n"
    "- A LOW or MEDIUM result does not rule out a serious condition. If a "
    "lesion changes, bleeds, or does not heal, refer the patient regardless "
    "of the AI result.\n"
    "- Final diagnosis and treatment decisions rest with qualified physicians "
    "only.\n\n"
    "Patient data is stored securely, used only for screening and follow-up, "
    "and every access is audit-logged. Screening requires explicit patient "
    "consent."
)
DISCLAIMER_VERSION = "1.0"
DISCLAIMER_UPDATED = "2026-10-15"


@compliance_bp.get("/disclaimer")
def get_disclaimer():
    """Public endpoint - no auth, so the disclaimer can be shown pre-login."""
    return ok(
        {
            "disclaimer_text": DISCLAIMER_TEXT,
            "version": DISCLAIMER_VERSION,
            "last_updated": DISCLAIMER_UPDATED,
        }
    )


@compliance_bp.post("/consent")
@require_auth
def record_consent():
    data = request.get_json(silent=True) or {}
    if not data.get("patient_id"):
        return err("patient_id is required", 400)
    screening = bool(data.get("consent_to_screening"))
    storage = bool(data.get("consent_to_data_storage"))
    if not screening and not storage:
        return err("At least one consent flag must be true", 400)

    try:
        patient_id = int(data["patient_id"])
    except (TypeError, ValueError):
        return err("patient_id must be a number", 400)
    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.phc_id not in phc_scope_ids(g.staff):
        return err("Patient not found", 404)

    record = Consent(
        patient_id=patient.id,
        phc_id=patient.phc_id,
        consent_to_screening=screening,
        consent_to_data_storage=storage,
    )
    db.session.add(record)
    db.session.flush()
    log_action("record_consent", patient.id, {"screening": screening, "storage": storage})
    db.session.commit()
    return ok(record.to_dict(), 201)
