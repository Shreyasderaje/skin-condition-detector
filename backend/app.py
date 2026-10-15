"""Flask entry point for the Skin Condition Detector backend.

Development:  python app.py            (http://localhost:5000)
Production:   gunicorn --bind 0.0.0.0:5000 app:app
"""
import logging
import os
import time

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from config import Config
from extensions import cors, db
from routes import register_routes
from utils.rate_limiter import check_rate_limit
from utils.responses import err

logging.basicConfig(level=logging.INFO)


def _init_db(app):
    """create_all with retries so the container can wait for PostgreSQL."""
    last_exc = None
    for attempt in range(30):
        try:
            with app.app_context():
                db.create_all()
            return
        except Exception as exc:  # noqa: BLE001 - any driver error means "not ready yet"
            last_exc = exc
            app.logger.warning("Database not ready (%s); retrying in 2s...", exc)
            time.sleep(2)
    raise last_exc


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    register_routes(app)  # imports models, so they exist before create_all
    _init_db(app)

    @app.before_request
    def apply_rate_limit():
        if request.path.startswith("/api/"):
            key = "ip:" + (request.remote_addr or "unknown")
            if not check_rate_limit(key, app.config["RATE_LIMIT_PER_MINUTE"]):
                return err(
                    f"Rate limit exceeded ({app.config['RATE_LIMIT_PER_MINUTE']} req/min)",
                    429,
                )
        return None

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(413)
    def payload_too_large(_e):
        return err(f"Payload too large (max {app.config['MAX_IMAGE_MB']}MB)", 413)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return err("Method not allowed", 405)

    @app.errorhandler(Exception)
    def handle_exception(exc):
        if isinstance(exc, HTTPException):
            return err(exc.description, exc.code)
        app.logger.exception("Unhandled server error")
        return err("Internal server error", 500)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
