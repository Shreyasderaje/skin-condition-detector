"""Application configuration. Every value can be overridden via environment/.env."""
import os

from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-this")
    JWT_EXPIRY_SECONDS = int(os.getenv("JWT_EXPIRY", "86400"))  # 24 hours

    # SQLite for local development by default; docker-compose points at PostgreSQL.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(basedir, "uploads"))
    MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "5"))
    MAX_CONTENT_LENGTH = MAX_IMAGE_MB * 1024 * 1024

    # Trained weights (ml/model.pth or ml/model.onnx). When absent the API
    # falls back to a clearly-flagged deterministic demo model.
    MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(basedir, "ml", "model.pth"))

    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    TESTING = False
