# ============================================================
#  UPLIFT CRM BACKEND CONFIGURATION (FINAL – RENDER READY)
# ============================================================

import os
from dotenv import load_dotenv
from pathlib import Path

# ------------------------------------------------------------
# Load .env automatically (both local + Render)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()  # fallback (Render env variables)

# ------------------------------------------------------------
# Environment Loader
# ------------------------------------------------------------
def env(key: str, default: str = "") -> str:
    """Read environment variable with safe fallback."""
    value = os.getenv(key, default)
    return value.strip() if isinstance(value, str) else value


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
    JWT_SECRET_KEY: str = env("JWT_SECRET_KEY", "upliftsecretkey123")
    JWT_ALGORITHM: str = env("JWT_ALGORITHM", "HS256")

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------
    DATABASE_URL: str = env("DATABASE_URL", "")

        # --------------------------------------------------------
    # Frontend & CORS
    # --------------------------------------------------------
    FRONTEND_BASE_URL: str = env("FRONTEND_BASE_URL", "http://localhost:4173")
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://192.168.29.70:5173",
        "http://192.168.29.70:4173",
        # --- ✅ Add these two Render URLs ---
        "https://uplift-crm-ui.onrender.com",
        "https://uplift-crm-os.onrender.com",
    ]

    _extra_front = env("FRONTEND_BASE_URL", "")
    if _extra_front and _extra_front not in CORS_ORIGINS:
        CORS_ORIGINS.append(_extra_front)

    # --------------------------------------------------------
    # Timezone / Localization
    # --------------------------------------------------------
    TIMEZONE: str = env("TZ", "Asia/Kolkata")

    # --------------------------------------------------------
    # Google OAuth / Integrations
    # --------------------------------------------------------
    BACKEND_BASE_URL: str = env("BACKEND_BASE_URL", "https://uplift-crm-os.onrender.com")
    GOOGLE_CLIENT_ID: str = env("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = env("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = env(
        "GOOGLE_REDIRECT_URI",
        f"{BACKEND_BASE_URL}/auth/google/callback",
    )

    # --------------------------------------------------------
    # AI / External APIs
    # --------------------------------------------------------
    HF_API_KEY: str = env("HF_API_KEY", "")
    OPENROUTER_API_KEY: str = env("OPENROUTER_API_KEY", "")


# Instantiate Settings
settings = Settings()

# ------------------------------------------------------------
# Debug mode check (local run)
# ------------------------------------------------------------
if __name__ == "__main__":
    print("✅ Loaded Settings")
    print("Project:", settings.PROJECT_NAME)
    print("Frontend URL:", settings.FRONTEND_BASE_URL)
    print("CORS Origins:", settings.CORS_ORIGINS)
    print("Backend URL:", settings.BACKEND_BASE_URL)
    print("Google Client ID:", "✔️" if settings.GOOGLE_CLIENT_ID else "❌ Not Set")
    print("Database URL:", "✔️" if settings.DATABASE_URL else "❌ Not Set")
