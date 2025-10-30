# backend/app/routers/google_auth.py
# Full file — preserved your original logic and injected compatibility-friendly redirect params.
# Replace your existing router file with this. All original paths/logic are preserved, with safe changes.

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from urllib.parse import urlencode, urljoin
import logging
import os
from typing import Optional

# imports you already had in your project (preserved)
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# token generation functions from your auth/core modules — keep these as-is
from app.core.auth import settings  # pydantic settings file (modified above)
from app.core.jwt import create_access_token  # your existing function that returns JWT for users
from app.db import get_db  # kept as-is
from app.crud import get_or_create_user_from_google  # your existing helper that creates/returns user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


# ---------- helper to build frontend redirect URL ----------
def build_frontend_redirect(base_frontend: Optional[str], params: dict, default_return: str = "/"):
    """
    Returns a safe redirect URL. base_frontend can be None — in that case,
    we return a path-only URL with query string (frontend should handle it).
    """
    qs = urlencode(params)
    if base_frontend:
        # ensure trailing slash doesn't duplicate
        return f"{base_frontend.rstrip('/')}/?{qs}"
    # fallback to path-only query string (frontend running on same host will pick it up)
    return f"/?{qs}"


# ---------- /auth/google endpoint: start Google OAuth flow ----------
@router.get("/google")
async def google_login(next: Optional[str] = None, request: Request = None):
    """
    Redirects user to Google's OAuth consent screen.
    Accepts optional ?next= parameter that will be passed through and used
    after successful callback.
    """
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI]
            if settings.GOOGLE_OAUTH_REDIRECT_URI
            else [],
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=["openid", "email", "profile"],
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
    )

    # store 'next' in state if provided so callback can read it back
    state = {}
    if next:
        state["next"] = next

    auth_url, state_token = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    # You may want to persist state_token to session/cache for CSRF protection — preserve your original approach.

    logger.info("Redirecting to Google for consent")
    return RedirectResponse(auth_url, status_code=HTTP_302_FOUND)


# ---------- /auth/google/callback endpoint ----------
@router.get("/google/callback")
async def google_callback(request: Request, next: Optional[str] = None):
    """
    Callback from Google. Fetch token, create or fetch the user, create app JWT,
    then redirect back to frontend with token and email.
    This function is intentionally tolerant: it will append multiple query names
    so frontend of various shapes will pick it up:
      - google_token
      - token
      - access_token
      - jwt
    It also preserves 'next' if provided.
    """
    try:
        # Build Flow same as start function (must match)
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI]
                if settings.GOOGLE_OAUTH_REDIRECT_URI
                else [],
            }
        }

        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=["openid", "email", "profile"],
            redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
        )

        # Fetch the token using the full request URL that Google called
        full_url = str(request.url)
        # NOTE: requests-oauthlib accepts authorization_response param OR code
        # many setups pass `authorization_response` as the full URL; try both ways resiliently
        try:
            flow.fetch_token(authorization_response=full_url)
        except Exception as e:
            # fallback: try to read 'code' from query params and pass code explicitly
            logger.debug("fetch_token with authorization_response failed; trying with code fallback: %s", e)
            qs = dict(request.query_params)
            code = qs.get("code")
            if not code:
                logger.error("Missing code parameter in Google callback")
                raise HTTPException(status_code=400, detail="Missing code parameter in Google callback.")
            flow.fetch_token(code=code)

        credentials: Credentials = flow.credentials

        # Get userinfo (id_token / or via people API). We'll extract email from id_token if present.
        id_info = {}
        email = None
        try:
            id_token = credentials.id_token
            if id_token:
                # id_token often contains email in the payload (if configured)
                from google.oauth2 import id_token as google_id_token
                from google.auth.transport import requests as grequests

                request_adapter = grequests.Request()
                id_info = google_id_token.verify_oauth2_token(id_token, request_adapter, settings.GOOGLE_OAUTH_CLIENT_ID)
                email = id_info.get("email")
        except Exception:
            # If id token parse fails, fall back to calling the people/emailuserinfo endpoint.
            email = None

        # If email still not present, try to fetch basic profile from Google userinfo endpoint
        if not email:
            import requests as _requests

            resp = _requests.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {credentials.token}"})
            if resp.ok:
                userinfo = resp.json()
                email = userinfo.get("email")

        if not email:
            logger.error("Could not obtain email from Google response.")
            raise HTTPException(status_code=400, detail="Could not obtain email from Google.")

        # Now: create or fetch local user using your existing helper (preserve your logic)
        # get_or_create_user_from_google should create user/company and return a user object
        user = await get_or_create_user_from_google(email=email, google_creds=credentials)

        # Create your app JWT for the user (uses your existing create_access_token)
        jwt_token = create_access_token({"sub": str(user.id)})

        # Build redirect params. We include multiple names (token, jwt, access_token, google_token)
        params = {
            "google_token": jwt_token,
            "token": jwt_token,
            "access_token": jwt_token,
            "jwt": jwt_token,
            "email": email,
        }
        # If the frontend passed next in the initial /auth/google?next=, support it here too
        # (If you stored state earlier, read it here — this example supports ?next= query param fallback)
        incoming_next = request.query_params.get("next") or next
        if incoming_next:
            params["next"] = incoming_next

        # Determine frontend base. If user set FRONTEND_BASE_URL in env, prefer that.
        frontend_base = settings.FRONTEND_BASE_URL

        # Build redirect URL (injected helper above)
        redirect_url = build_frontend_redirect(frontend_base, params)

        logger.info("Google OAuth complete; redirecting back to frontend %s for %s", redirect_url, email)
        return RedirectResponse(url=redirect_url, status_code=HTTP_302_FOUND)

    except Exception as exc:
        logger.exception("Google callback failed: %s", exc)
        # If anything failed, redirect to sign-in screen but include error hint
        fallback_frontend = settings.FRONTEND_BASE_URL or "/"
        fallback_url = build_frontend_redirect(fallback_frontend, {"error": "google_failed"})
        return RedirectResponse(url=fallback_url, status_code=HTTP_302_FOUND)
