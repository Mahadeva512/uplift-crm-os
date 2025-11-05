# backend/app/routers/auth.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# ✅ Unified Config Import
from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.company_profile import CompanyProfile

router = APIRouter(prefix="/auth", tags=["Auth"])

# ---------------------------------------------------------------------
# Security & JWT
# ---------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)

ALGORITHM = settings.JWT_ALGORITHM or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password with fallback for legacy users"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return plain == hashed


def hash_password(plain: str) -> str:
    """Hash password safely (bcrypt limit protection)"""
    return pwd_context.hash(plain[:72])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT using unified settings"""
    to_encode = {}
    for k, v in data.items():
        if isinstance(v, UUID):
            to_encode[k] = str(v)
        else:
            to_encode[k] = v

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

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


# ---------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------
@router.post("/signup", summary="Register new company and admin user")
def signup(payload: dict, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload["email"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

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
    db.flush()

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


# ---------------------------------------------------------------------
# Login (Form-data)
# ---------------------------------------------------------------------
@router.post("/login", summary="Login (Generate JWT)")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "company_id": str(user.company_id),
        "role": user.role,
    })
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------
# Get Current User
# ---------------------------------------------------------------------
@router.get("/me", summary="Get Logged-In User Info")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = db.query(CompanyProfile).filter(CompanyProfile.id == current_user.company_id).first()
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company_id": str(current_user.company_id),
        "company": {
            "id": str(company.id) if company else None,
            "company_name": getattr(company, "company_name", None),
            "theme_color": getattr(company, "theme_color", None),
            "accent_color": getattr(company, "accent_color", None),
            "footer_note": getattr(company, "footer_note", None),
        },
    }
