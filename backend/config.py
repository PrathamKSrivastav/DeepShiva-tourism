import os
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_JWT_SECRET = "your-super-secret-key-change-in-production-min-32-chars"


class Settings:
    # Environment
    ENV: str = os.getenv("ENV", "development").lower()

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/deepshiva_tourism")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "deepshiva_tourism")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", _DEFAULT_JWT_SECRET)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "168"))  # 7 days

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Admin Configuration
    ADMIN_EMAILS: list = [e.strip() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]

    # CORS — comma-separated list; FRONTEND_URL kept for backward compat
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS: list = [
        o.strip() for o in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000,https://deep-shiva-tourism.vercel.app",
        ).split(",") if o.strip()
    ]

    # API
    API_VERSION: str = "3.1.1"

    def validate_production(self):
        """Fail fast if production is misconfigured."""
        if self.ENV != "production":
            return
        errors = []
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET or len(self.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be set to a strong value (>=32 chars)")
        if not self.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID is required in production")
        if not os.getenv("GROQ_API_KEY"):
            errors.append("GROQ_API_KEY is required in production")
        if not os.getenv("QDRANT_HOST"):
            errors.append("QDRANT_HOST is required in production (Chroma fallback disabled)")
        if errors:
            raise RuntimeError("Production config errors: " + "; ".join(errors))


settings = Settings()
