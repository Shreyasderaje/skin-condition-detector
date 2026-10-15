"""Analytics endpoints for the PHC dashboard."""
from datetime import datetime, timedelta

from flask import Blueprint, g, request
from sqlalchemy import func

from extensions import utcnow
from models.consultation import Consultation
from utils.auth import phc_scope_ids, require_auth
from utils.responses import err, ok

analytics_bp = Blueprint("analytics", __name__)

RISK_KEYS = ["Low", "Medium", "High"]


def _base_query():
    return Consultation.query.filter(Consultation.phc_id.in_(phc_scope_ids(g.staff)))


def _apply_date_range(query, args):
    start, end = args.get("start_date"), args.get("end_date")
    try:
        if start:
            query = query.filter(Consultation.created_at >= datetime.fromisoformat(start))
        if end:
            query = query.filter(
                Consultation.created_at < datetime.fromisoformat(end) + timedelta(days=1)
            )
    except ValueError:
        raise ValueError("Invalid date filter (use YYYY-MM-DD)")
    return query


@analytics_bp.get("/analytics/summary")
@require_auth
def summary():
    try:
        query = _apply_date_range(_base_query(), request.args)
    except ValueError as exc:
        return err(str(exc), 400)

    total = query.count()

    risk_distribution = {key: 0 for key in RISK_KEYS}
    for level, count in (
        query.with_entities(Consultation.risk_level, func.count())
        .group_by(Consultation.risk_level)
        .all()
    ):
        key = (level or "").capitalize()
        if key in risk_distribution:
            risk_distribution[key] = count

    referred_count = query.filter(Consultation.referred_to_specialist.is_(True)).count()
    referral_rate = round(referred_count / total * 100, 1) if total else 0.0

    condition_breakdown = {
        (condition or "Unknown"): count
        for condition, count in (
            query.with_entities(Consultation.condition_type, func.count())
            .group_by(Consultation.condition_type)
            .all()
        )
    }

    referral_hours = [
        (referred_at - created_at).total_seconds() / 3600.0
        for created_at, referred_at in query.filter(
            Consultation.referred_to_specialist.is_(True),
            Consultation.referred_at.isnot(None),
        )
        .with_entities(Consultation.created_at, Consultation.referred_at)
        .all()
    ]
    avg_response = (
        round(sum(referral_hours) / len(referral_hours), 1) if referral_hours else None
    )

    return ok(
        {
            "total_consultations": total,
            "risk_distribution": risk_distribution,
            "referral_rate": referral_rate,
            "avg_response_time_hours": avg_response,
            "condition_breakdown": condition_breakdown,
        }
    )


@analytics_bp.get("/analytics/trends")
@require_auth
def trends():
    days_map = {"7days": 7, "30days": 30, "90days": 90}
    period = request.args.get("period", "30days")
    if period not in days_map:
        return err("period must be one of 7days, 30days, 90days", 400)
    days = days_map[period]

    since = utcnow() - timedelta(days=days)
    rows = (
        _base_query()
        .filter(Consultation.created_at >= since)
        .with_entities(Consultation.created_at, Consultation.risk_level)
        .all()
    )

    today = utcnow().date()
    points = {}
    for offset in range(days - 1, -1, -1):
        key = (today - timedelta(days=offset)).isoformat()
        points[key] = {"date": key, "total": 0, "Low": 0, "Medium": 0, "High": 0}
    for created_at, level in rows:
        key = created_at.date().isoformat()
        if key in points:
            points[key]["total"] += 1
            risk = (level or "").capitalize()
            if risk in ("Low", "Medium", "High"):
                points[key][risk] += 1

    return ok({"period": period, "points": list(points.values())})
