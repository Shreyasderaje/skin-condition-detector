"""Append-only audit trail of staff actions (compliance requirement)."""
from extensions import db, utcnow


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("phc_staff.id"), index=True)
    action = db.Column(db.String(60), nullable=False)  # upload_image, view_consultation, ...
    resource_id = db.Column(db.Integer)  # consultation / patient id the action touched
    ip_address = db.Column(db.String(45))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
