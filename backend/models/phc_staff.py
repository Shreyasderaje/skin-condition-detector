"""PHC staff accounts (each row is one staff member of one PHC)."""
from extensions import db, utcnow


class PhcStaff(db.Model):
    __tablename__ = "phc_staff"

    id = db.Column(db.Integer, primary_key=True)
    phc_name = db.Column(db.String(120), nullable=False, index=True)
    staff_name = db.Column(db.String(120), nullable=False)
    staff_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime)

    patients = db.relationship("Patient", backref="phc", lazy="dynamic")

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "phc_name": self.phc_name,
            "staff_name": self.staff_name,
            "staff_id": self.staff_id,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
