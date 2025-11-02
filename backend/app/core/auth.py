# backend/app/core/auth.py
# (Full file — injected FRONTEND_BASE_URL setting and kept other logic intact)

from typing import Optional
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    PROJECT_NAME: str = "Uplift CRM OS"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    # ------------------ INJECTED SAFE DEFAULT ------------------
    # If FRONTEND_BASE_URL is not provided in environment, keep None and code
    # that references it should handle None gracefully.
    FRONTEND_BASE_URL: Optional[str] = None
    # ----------------------------------------------------------
    # CORS / allowed origins (you may still override via env)
    ALLOWED_ORIGINS: Optional[str] = None

    # Google OAuth client config (should be provided as env vars)
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
