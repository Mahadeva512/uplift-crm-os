# app/routers/integrations/google_auth.py
from __future__ import annotations

import os, json, logging, uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# --- DB + Models -------------------------------------------------------------
try:
    from app.db.session import get_db
    from sqlalchemy.orm import Session
except Exception:
    get_db = None
    Session = None

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

# --- Auth token helper -------------------------------------------------------
try:
    from app.routers.auth import create_access_token
except Exception:
    import jwt
    SECRET_KEY = os.getenv("UPLIFT_SECRET_KEY", "dev-secret")
    ALGORITHM = "HS256"

    def create_access_token(data: dict, expires_delta: Optional[int] = None):
        expire = datetime.utcnow() + timedelta(minutes=120)
        data.update({"exp": expire})
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# --- Setup -------------------------------------------------------------------
logger = logging.getLogger("google_auth")
router = APIRouter()
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = ROOT / "routers" / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_SECRETS_FILE = str(CREDENTIALS_DIR / "google_oauth_client.json")

BACKEND_BASE = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_BASE = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
REDIRECT_URI = f"{BACKEND_BASE}/auth/google/callback"
FRONTEND_AFTER_GOOGLE = FRONTEND_BASE

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# --- Utility helpers ---------------------------------------------------------
def _require_client_secrets():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise HTTPException(500, "Missing google_oauth_client.json")

def _token_path(email: str) -> Path:
    safe = email.replace("/", "_")
    return CREDENTIALS_DIR / f"token_{safe}.json"

def _save_user_token(email: str, creds):
    p = _token_path(email)
    with open(p, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return str(p)

def _load_user_token(email: str):
    p = _token_path(email)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _delete_user_token(email: str):
    try:
        _token_path(email).unlink(missing_ok=True)
    except Exception:
        pass

# --- Auto-create company + user ---------------------------------------------
def _create_placeholder_company(db: Session, full_name: str, email: str):
    """Make '<first>' (Company) record if not present."""
    if not CompanyModel or not db:
        return None
    try:
        first = (full_name or email.split("@")[0]).split()[0]
        name = f"{first}'s Company"
        company = CompanyModel(
            id=str(uuid.uuid4()),
            company_name=name,
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
    """Return user if exists else create new user + placeholder company."""
    if not (db and UserModel):
        return None
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user:
        return user

    company = _create_placeholder_company(db, full_name, email)
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
        return user
    except Exception as e:
        logger.error("User creation failed: %s", e, exc_info=True)
        db.rollback()
        return None

# --- Routes ------------------------------------------------------------------
@router.get("/auth/google")
def google_login(select_account: bool = Query(default=True)):
    _require_client_secrets()
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        prompt="consent" if select_account else "none",
        access_type="offline",
        include_granted_scopes="true",
    )
    return RedirectResponse(auth_url)

@router.get("/auth/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db) if get_db else None):
    _require_client_secrets()
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing authorization code")

    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    creds = flow.credentials

    me = build("oauth2", "v2", credentials=creds).userinfo().get().execute()
    email = me.get("email")
    full_name = me.get("name") or me.get("given_name") or (email.split("@")[0] if email else "")
    if not email:
        raise HTTPException(500, "Google did not return an email")

    _save_user_token(email, creds)
    user = _provision_user_if_needed(db, email, full_name)

    payload = {"email": email}
    if user:
        payload["sub"] = str(getattr(user, "id", email))
        payload["role"] = getattr(user, "role", "user")
        payload["company_id"] = str(getattr(user, "company_id", "")) or ""
    crm_jwt = create_access_token(payload)

    return RedirectResponse(f"{FRONTEND_AFTER_GOOGLE}?google_token={crm_jwt}&email={email}")

@router.get("/auth/google/status")
def google_status(user_email: str):
    if _load_user_token(user_email):
        return {"connected": True}
    raise HTTPException(404, "No Gmail connection for this user")

@router.post("/auth/google/disconnect")
def google_disconnect(user_email: str):
    _delete_user_token(user_email)
    return JSONResponse({"ok": True})
