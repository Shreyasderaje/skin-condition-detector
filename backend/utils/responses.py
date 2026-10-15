"""Consistent JSON response helpers."""
import uuid

from flask import jsonify


def ok(data=None, status=200):
    return jsonify(data if data is not None else {}), status


def err(message, status=400, error_id=None):
    payload = {"error": message}
    if status >= 500:
        payload["error_id"] = error_id or uuid.uuid4().hex[:8]
    return jsonify(payload), status
