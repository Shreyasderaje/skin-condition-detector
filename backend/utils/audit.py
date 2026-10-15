"""Audit-trail helper. Rows are committed together with the caller's
transaction so an action and its audit entry are atomic."""
from flask import g, request

from extensions import db
from models.audit_log import AuditLog


def log_action(action, resource_id=None, details=None):
    staff = getattr(g, "staff", None)
    entry = AuditLog(
        user_id=staff.id if staff is not None else None,
        action=action,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        details=details,
    )
    db.session.add(entry)
    return entry
