"""Patient records created during intake at a PHC."""
from extensions import db, utcnow


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    phc_id = db.Column(db.Integer, db.ForeignKey("phc_staff.id"), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    location = db.Column(db.String(120), nullable=False)  # taluka
    contact_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    consultations = db.relationship("Consultation", backref="patient", lazy="dynamic")
    consents = db.relationship("Consent", backref="patient", lazy="dynamic")

    def to_dict(self):
        return {
            "patient_id": self.id,
            "age": self.age,
            "gender": self.gender,
            "location": self.location,
            "contact_number": self.contact_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
