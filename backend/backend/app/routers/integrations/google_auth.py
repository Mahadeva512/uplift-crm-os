from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.models import User
from app.core.auth import create_access_token
from app.db import get_db
import os

router = APIRouter(prefix="/auth/google", tags=["Google Auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://uplift-crm-backend.onrender.com")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:4173")

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": "uplift-crm",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [f"{BACKEND_BASE_URL}/auth/google/callback"],
        }
    },
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
)

@router.get("/login")
async def google_login():
    authorization_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    return RedirectResponse(authorization_url)

@router.get("/callback")
async def google_callback(request: Request):
    db = next(get_db())
    try:
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        email = user_info.get("email")
        name = user_info.get("name")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            redirect_url = f"{FRONTEND_BASE_URL}/onboarding?name={name}&email={email}"
        else:
            token = create_access_token({"sub": user.email})
            redirect_url = f"{FRONTEND_BASE_URL}/?token={token}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
