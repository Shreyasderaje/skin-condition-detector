"""Shared Flask extension instances and small common helpers."""
from datetime import datetime, timezone

from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()


def utcnow():
    """Naive UTC timestamp used consistently for all DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
