"""One screening consultation: an uploaded image plus its AI risk assessment."""
from extensions import db, utcnow


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    # Denormalised creator-PHC id (== patient.phc_id) so list/analytics queries
    # can scope by PHC without a join.
    phc_id = db.Column(db.Integer, db.ForeignKey("phc_staff.id"), nullable=False, index=True)

    image_path = db.Column(db.String(255), nullable=False)  # filename inside UPLOAD_FOLDER
    model_mode = db.Column(db.String(10), default="demo")  # torch | onnx | demo
    risk_level = db.Column(db.String(10), nullable=False)  # LOW / MEDIUM / HIGH
    confidence_scores = db.Column(db.JSON)  # {"Low": 0.05, "Medium": 0.10, "High": 0.85}
    condition_type = db.Column(db.String(60))

    staff_notes = db.Column(db.Text)
    vitals_temp = db.Column(db.Float)  # °C, optional

    referred_to_specialist = db.Column(db.Boolean, default=False, index=True)
    referral_reason = db.Column(db.Text)
    referral_urgency = db.Column(db.String(20))  # Routine / Urgent / Emergency
    referral_specialist = db.Column(db.String(60))
    referred_at = db.Column(db.DateTime)
    follow_up_date = db.Column(db.Date)
    outcome = db.Column(db.String(20))  # healed / ongoing / escalated (filled at follow-up)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self, include_patient=False):
        data = {
            "consultation_id": self.id,
            "patient_id": self.patient_id,
            "image_url": f"/api/consultations/{self.id}/image",
            "model_mode": self.model_mode,
            "risk_level": self.risk_level,
            "confidence": self.confidence_scores or {},
            "condition_type": self.condition_type,
            "staff_notes": self.staff_notes,
            "vitals_temp": self.vitals_temp,
            "referred_to_specialist": bool(self.referred_to_specialist),
            "referral_reason": self.referral_reason,
            "referral_urgency": self.referral_urgency,
            "referral_specialist": self.referral_specialist,
            "referred_at": self.referred_at.isoformat() if self.referred_at else None,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_patient and self.patient is not None:
            data["patient"] = self.patient.to_dict()
        return data
