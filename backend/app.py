
"""Flask entry point for the Skin Condition Detector backend.

Development:  python app.py
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

# Your deployed React + Vite frontend.
FRONTEND_ORIGINS = [
    "https://skin-condition-detector.vercel.app",
]


def _init_db(app):
    """Create database tables, retrying while PostgreSQL becomes available."""
    last_exc = None

    for attempt in range(30):
        try:
            with app.app_context():
                db.create_all()
            app.logger.info("Database initialized successfully.")
            return
        except Exception as exc:
            last_exc = exc
            app.logger.warning(
                "Database not ready (attempt %s/30): %s; retrying in 2s...",
                attempt + 1,
                exc,
            )
            time.sleep(2)

    raise last_exc


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize database.
    db.init_app(app)

    # Allow the deployed frontend to access authentication and API routes.
    # Flask-CORS handles preflight requests for registered routes.
    cors.init_app(
        app,
        resources={
            r"/auth/.*": {
                "origins": FRONTEND_ORIGINS,
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": [
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                ],
            },
            r"/api/.*": {
                "origins": FRONTEND_ORIGINS,
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": [
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                ],
            },
        },
    )

    # Register blueprints before creating database tables.
    register_routes(app)

    # Initialize database.
    _init_db(app)

    @app.before_request
    def apply_rate_limit():
        if request.path.startswith("/api/"):
            key = "ip:" + (request.remote_addr or "unknown")

            if not check_rate_limit(
                key,
                app.config["RATE_LIMIT_PER_MINUTE"],
            ):
                return err(
                    f"Rate limit exceeded "
                    f"({app.config['RATE_LIMIT_PER_MINUTE']} req/min)",
                    429,
                )

        return None

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(413)
    def payload_too_large(_exc):
        return err(
            f"Payload too large (max {app.config['MAX_IMAGE_MB']}MB)",
            413,
        )

    @app.errorhandler(405)
    def method_not_allowed(_exc):
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

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )
