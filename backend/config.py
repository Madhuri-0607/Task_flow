import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url):
    """Railway provides postgres:// but SQLAlchemy 1.4+ requires postgresql://"""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Production Configuration"""
    
    # ─── Session & Cookies ─────────────────────────────────────────────────
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # ─── Database ──────────────────────────────────────────────────────────
    _raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///taskmanager.db")
    SQLALCHEMY_DATABASE_URI = _fix_db_url(_raw_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings - critical for Railway PostgreSQL stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,        # Detect stale connections before using them
        "pool_recycle": 280,          # Recycle before Railway's ~300s timeout
        "pool_size": 5,
        "max_overflow": 10,
        "echo": False,                # Set to True for SQL debugging
    }
    
    # ─── JWT Configuration ─────────────────────────────────────────────────
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "jwt-secret-key-change-in-production"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = "HS256"
    
    # ─── Request Handling ──────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request size
    JSON_SORT_KEYS = False
    
    # ─── Flask Environment ─────────────────────────────────────────────────
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
