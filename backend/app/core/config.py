# ============================================================
#  UPLIFT CRM BACKEND CONFIGURATION (FINAL – DOTENV VERSION)
# ============================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local) or Render dashboard (production)
load_dotenv()


class Settings:
    # --------------------------------------------------------
    # Core Project Info
    # --------------------------------------------------------
    PROJECT_NAME: str = "Uplift CRM Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API for Uplift CRM OS"

    # --------------------------------------------------------
    # Security & JWT
    # --------------------------------------------------------
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "upliftsecretkey123")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # --------------------------------------------------------
    # Database Connection
    # --------------------------------------------------------
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # --------------------------------------------------------
    # Frontend & CORS
    # --------------------------------------------------------
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:4173")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # --------------------------------------------------------
    # Timezone / Localization
    # --------------------------------------------------------
    TIMEZONE: str = os.getenv("TZ", "Asia/Kolkata")

    # --------------------------------------------------------
    # Optional Integrations (Google, HF API, etc.)
    # --------------------------------------------------------
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")


# Instantiate settings
settings = Settings()

# Optional helper for quick debugging
if __name__ == "__main__":
    print("Loaded settings ✅")
    print("DB URL:", settings.DATABASE_URL or "Not set")
    print("Frontend URL:", settings.FRONTEND_BASE_URL)
    print("CORS Origins:", settings.CORS_ORIGINS)
