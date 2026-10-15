"""Patient consent records (screening and/or data storage)."""
from extensions import db, utcnow


class Consent(db.Model):
    __tablename__ = "consents"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    phc_id = db.Column(db.Integer, db.ForeignKey("phc_staff.id"), nullable=False)
    consent_to_screening = db.Column(db.Boolean, default=False, nullable=False)
    consent_to_data_storage = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "consent_record_id": self.id,
            "patient_id": self.patient_id,
            "consent_to_screening": bool(self.consent_to_screening),
            "consent_to_data_storage": bool(self.consent_to_data_storage),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
