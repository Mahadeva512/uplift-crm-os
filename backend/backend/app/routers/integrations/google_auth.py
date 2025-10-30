from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
import os, requests

router = APIRouter(prefix="/auth", tags=["Google OAuth"])

# ---- Load environment values ----
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://uplift-crm-backend.onrender.com/auth/google/callback"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@router.get("/google")
def google_login():
    """Start Google OAuth flow."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google credentials missing.")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_url, _ = flow.authorization_url(
        prompt="consent", access_type="offline", include_granted_scopes="true"
    )
    return RedirectResponse(authorization_url)


@router.get("/google/callback")
def google_callback(request: Request):
    """Handle redirect from Google and return user info."""
    full_url = str(request.url)
    if "code=" not in full_url:
        raise HTTPException(status_code=400, detail="Missing code parameter in callback URL.")

    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = REDIRECT_URI
        flow.fetch_token(authorization_response=full_url)
        credentials = flow.credentials

        # ---- Get profile ----
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        profile = resp.json()

        # (Optional) insert / fetch user from DB here
        return JSONResponse(
            content={
                "email": profile.get("email"),
                "name": profile.get("name"),
                "picture": profile.get("picture"),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
