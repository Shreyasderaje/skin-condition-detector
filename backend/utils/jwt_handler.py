"""JWT creation/verification for PHC staff sessions (24h expiry by default)."""
from datetime import datetime, timedelta, timezone

import jwt

from config import Config


def create_token(staff):
    payload = {
        "sub": staff.id,
        "staff_code": staff.staff_id,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=Config.JWT_EXPIRY_SECONDS),
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """Raise jwt.ExpiredSignatureError / jwt.InvalidTokenError on failure."""
    return jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
