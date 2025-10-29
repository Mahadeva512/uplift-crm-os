from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.company_profile import CompanyProfile

router = APIRouter(prefix="/auth", tags=["Auth"])

# ===================== Security & JWT =====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password hash with backward safety for legacy users"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # fallback for legacy plain-text passwords (not secure but avoids crash)
        return plain == hashed


def hash_password(plain: str) -> str:
    """Hash password safely"""
    return pwd_context.hash(plain[:72])  # bcrypt max limit safeguard


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT token safely (convert UUIDs to str)"""
    to_encode = {}
    for k, v in data.items():
        # Convert UUIDs and other non-JSON-safe objects to strings
        if isinstance(v, UUID):
            to_encode[k] = str(v)
        else:
            to_encode[k] = v

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


# ===================== Dependencies =====================
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Extract current user from JWT"""
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Convert user_id to UUID safely
        try:
            user_id = UUID(user_id_raw)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


# ===================== Routes =====================

@router.post("/signup", summary="Register new company and admin user")
def signup(payload: dict, db: Session = Depends(get_db)):
    """
    Body Example:
    {
        "full_name": "Admin User",
        "email": "owner@123.com",
        "password": "admin123",
        "company_name": "Uplift",
        "theme_color": "#0048E8",      (optional)
        "accent_color": "#FACC15",     (optional)
        "footer_note": "Thank you!"    (optional)
    }
    """
    # --- Check if email already exists ---
    existing = db.query(User).filter(User.email == payload["email"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # --- Create company profile ---
    company = CompanyProfile(
        company_name=payload["company_name"],
        email=payload["email"],
        theme_color=payload.get("theme_color", "#0048E8"),
        accent_color=payload.get("accent_color", "#FACC15"),
        footer_note=payload.get("footer_note", "Thank you for your business!"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(company)
    db.flush()  # fetch company.id before commit

    # --- Create admin user ---
    user = User(
        email=payload["email"],
        full_name=payload["full_name"],
        hashed_password=hash_password(payload["password"]),
        role="admin",
        is_active=True,
        company_id=company.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # --- Return confirmation ---
    return {
        "message": "Signup successful",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company_id": str(user.company_id),
        },
        "company": {
            "id": str(company.id),
            "company_name": company.company_name,
            "theme_color": company.theme_color,
            "accent_color": company.accent_color,
            "footer_note": company.footer_note,
        },
    }


# ==========================================================
#  ✅ Robust OAuth2 Login (Form-data compatible with Swagger)
# ==========================================================
@router.post("/login", summary="Login (Generate JWT)")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Accepts form-data (Swagger-compatible):
    username=<email>
    password=<password>
    """

    # 🔍 Find user by email (username field holds email)
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 🧾 Generate and return JWT (convert UUIDs to str)
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "company_id": str(user.company_id),
        "role": user.role
    })

    return {"access_token": token, "token_type": "bearer"}


# ==========================================================
#  ✅ Authenticated user info
# ==========================================================
@router.get(
    "/me",
    summary="Get Logged-In User Info",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return user + company details of the logged-in user"""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == current_user.company_id).first()
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company_id": str(current_user.company_id),
        "company": {
            "id": str(company.id) if company else None,
            "company_name": company.company_name if company else None,
            "theme_color": getattr(company, "theme_color", None),
            "accent_color": getattr(company, "accent_color", None),
            "footer_note": getattr(company, "footer_note", None),
        },
    }
# ==========================================================
#  🌐 GOOGLE OAUTH LOGIN (LIVE READY FOR RENDER)
# ==========================================================
from os import getenv
from fastapi import Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

import pathlib

GOOGLE_CLIENT_ID = getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = getenv("GOOGLE_OAUTH_CLIENT_SECRET")
BACKEND_URL = getenv("BACKEND_URL", "https://uplift-crm-backend.onrender.com")
FRONTEND_URL = getenv("FRONTEND_URL", "http://localhost:4173")
GOOGLE_REDIRECT_URI = getenv("GOOGLE_OAUTH_REDIRECT_URI", f"{BACKEND_URL}/auth/google/callback")

# ✅ OAuth Flow Configuration
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

@router.get("/google", summary="Start Google OAuth flow")
def google_login():
    """
    Redirect user to Google OAuth consent screen.
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    return RedirectResponse(auth_url)


@router.get("/google/callback", summary="Handle Google OAuth callback")
def google_callback(request: Request):
    """
    Handle Google OAuth redirect after login.
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = GOOGLE_REDIRECT_URI

    # Exchange code for tokens
    flow.fetch_token(authorization_response=str(request.url))

    # Extract user info
    credentials = flow.credentials
    from googleapiclient.discovery import build
    oauth2 = build("oauth2", "v2", credentials=credentials)
    user_info = oauth2.userinfo().get().execute()

    # TODO: you can create or fetch user in DB here

    # Redirect to frontend (post-login success)
    return RedirectResponse(f"{FRONTEND_URL}/")
