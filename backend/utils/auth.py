"""Authentication decorator + PHC data-scoping helpers."""
from functools import wraps

from flask import g, request

from extensions import db
from models.phc_staff import PhcStaff
from utils.jwt_handler import decode_token
from utils.responses import err


def require_auth(fn):
    """Verifies the Bearer token and loads g.staff before the view runs."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return err("Missing or invalid Authorization header", 401)
        token = header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except Exception:
            return err("Invalid or expired token", 401)
        staff = db.session.get(PhcStaff, payload.get("sub"))
        if staff is None:
            return err("Account no longer exists", 401)
        g.staff = staff
        return fn(*args, **kwargs)

    return wrapper


def phc_scope_ids(staff):
    """IDs of staff records belonging to the same PHC.

    Everyone registered under the same phc_name shares the patient list,
    so a PHC is a shared workspace; different PHCs are fully isolated.
    """
    rows = (
        db.session.query(PhcStaff.id).filter(PhcStaff.phc_name == staff.phc_name).all()
    )
    ids = [row.id for row in rows]
    return ids or [staff.id]
