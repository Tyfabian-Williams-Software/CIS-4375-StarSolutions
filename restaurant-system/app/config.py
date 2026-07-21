import os
from dotenv import load_dotenv

# Load .env from the PROJECT ROOT by explicit path, so it works no matter
# which directory the app is launched from.
_DOTENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(_DOTENV_PATH)

# Absolute path so the dev database is always <project-root>/dev.db, no matter
# which directory the app was launched from.
_DEV_DB = "sqlite:///" + os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dev.db")
).replace("\\", "/")


class Config:
    # Fall back to a local SQLite file for development so the app runs
    # out-of-the-box without a MySQL server. Production must set DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _DEV_DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    @staticmethod
    def validate_production():
        """Fail fast if running production with unsafe settings."""
        if os.getenv("FLASK_ENV", "production") == "production":
            if os.getenv("SECRET_KEY") in (None, "", "dev-only-change-me",
                                           "replace-me-with-a-secure-random-value"):
                raise RuntimeError(
                    "SECRET_KEY must be set to a secure random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if not os.getenv("DATABASE_URL"):
                raise RuntimeError("DATABASE_URL must be set in production.")
