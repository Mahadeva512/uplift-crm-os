import os

# ==========================================================
# 🔐 Uplift Global Auth Configuration
# ==========================================================

# JWT token setup
SECRET_KEY = os.getenv("UPLIFT_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("UPLIFT_TOKEN_MINUTES", "120"))

# ==========================================================
# 🌍 Google OAuth Setup (from environment variables)
# ==========================================================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "uplift-crm")

GOOGLE_CREDS = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [
            "https://uplift-crm-backend.onrender.com/auth/google/callback"
        ],
    }
}
