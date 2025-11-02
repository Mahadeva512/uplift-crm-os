from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# -----------------------------------------------------------------------------
# DB + models
# -----------------------------------------------------------------------------
try:
    from app.db.session import get_db
    from sqlalchemy.orm import Session
except Exception:
    get_db = None  # type: ignore
    Session = None  # type: ignore

UserModel = None
CompanyModel = None

try:
    from app.models.users import User as UserModel
except Exception:
    try:
        from app.models.user import User as UserModel
    except Exception:
        pass

try:
    from app.models.company_profile import CompanyProfile as CompanyModel
except Exception:
    try:
        from app.models.company import Company as CompanyModel
    except Exception:
        pass

# -----------------------------------------------------------------------------
# JWT helper
# -----------------------------------------------------------------------------
try:
    from app.routers.auth import create_access_token
except Exception:
    import jwt  # type: ignore

    SECRET_KEY = os.getenv("UPLIFT_SECRET_KEY", "dev-secret")
    ALGORITHM = "HS256"

    def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
        minutes = 120 if expires_delta is None else int(expires_delta)
        payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=minutes)}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------------------------------------------------------
# Setup & constants
# -----------------------------------------------------------------------------
logger = logging.getLogger("google_auth")
router = APIRouter()

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = ROOT / "routers" / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)


def _token_path(email: str) -> Path:
    safe = (email or "").replace("/", "_")
    return CREDENTIALS_DIR / f"token_{safe}.json"


BACKEND_BASE = os.getenv("BACKEND_BASE_URL", "https://uplift-crm-backend.onrender.com").rstrip("/")
FRONTEND_BASE = os.getenv("FRONTEND_BASE_URL", "http://localhost:4173").rstrip("/")
REDIRECT_URI = f"{BACKEND_BASE}/auth/google/callback"
FRONTEND_AFTER_GOOGLE = FRONTEND_BASE or "http://localhost:4173"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

from app.core.auth_config import GOOGLE_CREDS


def _require_client_secrets() -> dict:
    try:
        web = GOOGLE_CREDS["web"]
        if not web.get("client_id") or not web.get("client_secret"):
            raise KeyError("client_id/client_secret missing")
    except Exception as e:
        logger.error("Missing Google OAuth env config: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Missing Google OAuth credentials in environment variables",
        )
    return GOOGLE_CREDS


def _save_user_token(email: str, creds) -> None:
    p = _token_path(email)
    with open(p, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def _load_user_token(email: str):
    p = _token_path(email)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _delete_user_token(email: str) -> None:
    try:
        _token_path(email).unlink(missing_ok=True)
    except Exception:
        pass


def _create_placeholder_company(db: Session, full_name: str, email: str):
    if not CompanyModel or not db:
        return None
    try:
        first = (full_name or email.split("@")[0]).split()[0]
        company = CompanyModel(
            id=str(uuid.uuid4()),
            company_name=f"{first}'s Company",
            email=email,
            theme_color="#0C1428",
            accent_color="#FACC15",
            footer_note="Powered by Uplift CRM OS",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(company)
        db.flush()
        return company
    except Exception as e:
        logger.warning("Company creation failed: %s", e)
        db.rollback()
        return None


def _provision_user_if_needed(db: Session, email: str, full_name: Optional[str]):
    if not (db and UserModel):
        return None, False
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user:
        return user, False
    company = _create_placeholder_company(db, full_name or "", email)
    try:
        user = UserModel(
            id=str(uuid.uuid4()),
            email=email,
            full_name=full_name or email,
            hashed_password="",
            role="admin",
            is_active=True,
            company_id=getattr(company, "id", None),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True
    except Exception as e:
        logger.error("User creation failed: %s", e, exc_info=True)
        db.rollback()
        return None, False


def _build_frontend_redirect(base_url: str, token: str, email: str, is_new: bool, next_param: Optional[str]) -> str:
    from urllib.parse import urlencode
    target = (next_param or "").strip() or base_url
    qs = urlencode({"google_token": token, "email": email, "is_new": "1" if is_new else "0"})
    glue = "&" if ("?" in target) else "?"
    return f"{target}{glue}{qs}"


@router.get("/auth/google", name="google_login")
def google_login(next: Optional[str] = Query(default=None), select_account: bool = Query(default=True)):
    creds_dict = _require_client_secrets()
    flow = Flow.from_client_config(creds_dict, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        prompt="consent" if select_account else "none",
        access_type="offline",
        include_granted_scopes="true",
        state=next or "",
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback", name="google_callback")
def google_callback(request: Request, db: Session = Depends(get_db) if get_db else None):
    code = request.query_params.get("code")
    if not code:
        err = request.query_params.get("error") or "Missing authorization code"
        raise HTTPException(status_code=400, detail=str(err))

    next_param = request.query_params.get("state")

    creds_dict = _require_client_secrets()
    flow = Flow.from_client_config(creds_dict, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error("Google token exchange failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to fetch token from Google")

    creds = flow.credentials
    me = build("oauth2", "v2", credentials=creds).userinfo().get().execute()
    email = me.get("email")
    full_name = me.get("name") or me.get("given_name") or (email.split("@")[0] if email else "")
    if not email:
        raise HTTPException(status_code=500, detail="Google did not return an email")

    _save_user_token(email, creds)
    user, is_new = _provision_user_if_needed(db, email, full_name)

    payload = {"email": email}
    if user:
        payload["sub"] = str(getattr(user, "id", email))
        payload["role"] = getattr(user, "role", "user")
        payload["company_id"] = str(getattr(user, "company_id", "")) or ""
    crm_jwt = create_access_token(payload)

    redirect_url = _build_frontend_redirect(
        base_url=FRONTEND_AFTER_GOOGLE,
        token=crm_jwt,
        email=email,
        is_new=is_new,
        next_param=next_param,
    )
    return RedirectResponse(redirect_url)


@router.get("/auth/google/status")
def google_status(user_email: str):
    if _load_user_token(user_email):
        return {"connected": True}
    raise HTTPException(status_code=404, detail="No Gmail connection for this user")


@router.post("/auth/google/disconnect")
def google_disconnect(user_email: str):
    _delete_user_token(user_email)
    return JSONResponse({"ok": True})
