"""Authentication endpoints: register, login, logout (JWT Bearer)."""
import secrets

from flask import Blueprint, request

from extensions import db, utcnow
from models.phc_staff import PhcStaff
from utils.audit import log_action
from utils.auth import require_auth
from utils.jwt_handler import create_token
from utils.responses import err, ok
from utils.validators import validate_email, validate_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    for field in ("staff_name", "phc_name", "email", "password"):
        if not data.get(field):
            return err(f"Missing required field: {field}", 400)
    email = data["email"].strip().lower()
    if not validate_email(email):
        return err("Invalid email address", 400)
    if not validate_password(data["password"]):
        return err("Password must be at least 8 characters", 400)
    if db.session.query(PhcStaff.id).filter_by(email=email).first() is not None:
        return err("Email already registered", 409)

    staff = PhcStaff(
        phc_name=data["phc_name"].strip(),
        staff_name=data["staff_name"].strip(),
        email=email,
        phone=data.get("phone") or None,
    )
    while True:  # generate a unique public staff code
        staff.staff_id = "STF-" + secrets.token_hex(3).upper()
        if db.session.query(PhcStaff.id).filter_by(staff_id=staff.staff_id).first() is None:
            break
    staff.set_password(data["password"])
    db.session.add(staff)
    db.session.flush()
    log_action("register", staff.id)
    db.session.commit()
    return ok(
        {
            "access_token": create_token(staff),
            "staff_id": staff.staff_id,
            "staff": staff.to_dict(),
        },
        201,
    )


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    staff = db.session.query(PhcStaff).filter_by(email=email).first()
    if staff is None or not staff.check_password(data.get("password") or ""):
        return err("Invalid email or password", 401)
    staff.last_login = utcnow()
    log_action("login", staff.id)
    db.session.commit()
    return ok(
        {
            "access_token": create_token(staff),
            "staff_id": staff.staff_id,
            "phc_name": staff.phc_name,
            "staff": staff.to_dict(),
        }
    )


@auth_bp.post("/auth/logout")
@require_auth
def logout():
    log_action("logout")
    db.session.commit()
    return ok({"success": True})
