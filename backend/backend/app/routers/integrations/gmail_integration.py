# app/routers/integrations/gmail_integration.py
"""
Per-user Gmail integration for Uplift CRM.
- Tokens are stored per-user as: app/routers/credentials/token_<user_email>.json
- If a user logged in without Gmail scopes, they can later /connect to upgrade.

Exposed routes (prefix /integrations/gmail):
  GET  /connect?user_email=...         -> start OAuth (consent)
  GET  /callback                       -> finish OAuth; persist token
  GET  /status?user_email=...          -> { connected: bool }
  GET  /messages/{contact_email}       -> recent messages to/from that contact
  GET  /unread-count/{contact_email}   -> unread count to/from that contact (INBOX)
  POST /reply                          -> send mail using user's account
"""
from __future__ import annotations
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow

router = APIRouter(prefix="/integrations/gmail", tags=["Gmail Integration"])

# ---------- paths/scopes ----------
ROOT = Path(__file__).resolve().parents[2]  # .../app
CREDENTIALS_DIR = ROOT / "routers" / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_FILE = CREDENTIALS_DIR / "google_oauth_client.json"

BACKEND_BASE = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
REDIRECT_URI = f"{BACKEND_BASE}/integrations/gmail/callback"

# Scopes cover read, send, and modify (for reliable unread detection).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# ---------- helpers ----------
def _token_path_for(email: str) -> Path:
    return CREDENTIALS_DIR / f"token_{email}.json"

def _load_creds(email: str) -> Optional[Credentials]:
    p = _token_path_for(email)
    if not p.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(p))
        # Refresh if needed (writes refreshed token)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            p.write_text(creds.to_json(), encoding="utf-8")
        return creds
    except Exception as e:
        print(f"[gmail] failed loading creds for {email}: {e}")
        return None

def _service_for(email: str):
    creds = _load_creds(email)
    if not creds:
        return None
    # cache-less build; light weight enough
    return build("gmail", "v1", credentials=creds)

def _require_user_email(request: Request) -> str:
    email = request.headers.get("X-User-Email") or request.query_params.get("user_email")
    if not email:
        raise HTTPException(status_code=400, detail="Missing signed-in user (X-User-Email header or user_email query).")
    return email

# ---------- OAuth connect/callback ----------
@router.get("/connect")
def connect(user_email: str):
    if not CLIENT_FILE.exists():
        raise HTTPException(status_code=500, detail="Missing google_oauth_client.json")
    flow = Flow.from_client_secrets_file(str(CLIENT_FILE), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # store (state -> user_email) transiently
    (CREDENTIALS_DIR / f"state_{user_email}.json").write_text(json.dumps({"state": state}), encoding="utf-8")
    return RedirectResponse(auth_url)

@router.get("/callback")
def callback(state: str | None = None, code: str | None = None):
    # map state back to user email
    user_email = None
    for f in CREDENTIALS_DIR.glob("state_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("state") == state:
                user_email = f.stem.replace("state_", "")
                break
        except Exception:
            pass
    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    flow = Flow.from_client_secrets_file(str(CLIENT_FILE), scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    creds = flow.credentials
    _token_path_for(user_email).write_text(creds.to_json(), encoding="utf-8")
    # You can redirect to the frontend if you prefer:
    # return RedirectResponse("http://localhost:5173?gmail=connected")
    return JSONResponse({"message": f"Gmail connected for {user_email}"})

@router.get("/status")
def status(user_email: str):
    return {"connected": _token_path_for(user_email).exists()}

# ---------- read ----------
@router.get("/messages/{contact_email}")
def messages(contact_email: str, request: Request, limit: int = 5):
    """Recent messages to/from contact (subject/from/snippet)."""
    user_email = _require_user_email(request)
    svc = _service_for(user_email)
    if not svc:
        return {"messages": [], "status": "no_token"}
    try:
        q = f'from:"{contact_email}" OR to:"{contact_email}"'
        resp = svc.users().messages().list(userId="me", q=q, maxResults=max(1, min(limit, 25))).execute() or {}
        items = []
        for m in resp.get("messages", []):
            full = svc.users().messages().get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
            items.append({
                "id": m["id"],
                "subject": headers.get("Subject", "(No subject)"),
                "from": headers.get("From", ""),
                "snippet": full.get("snippet", ""),
            })
        return {"messages": items, "status": "ok"}
    except Exception as e:
        return {"messages": [], "status": "error", "detail": str(e)}

@router.get("/unread-count/{contact_email}")
def unread_count(contact_email: str, request: Request):
    """
    Returns unread message count in INBOX to/from contact_email for the signed-in user.
    We use labelIds=['UNREAD','INBOX'] + a narrow 'q' to avoid heavy searches.
    """
    user_email = _require_user_email(request)
    svc = _service_for(user_email)
    if not svc:
        # Distinguish "no token" from 404s and other errors on the frontend
        return {"count": 0, "status": "no_token"}

    try:
        # Narrow query: unread in inbox and either direction with contact.
        # Gmail ignores labelIds if q explicitly says -is:unread, etc., so keep it consistent.
        q = f'(from:"{contact_email}" OR to:"{contact_email}")'
        label_ids = ["UNREAD", "INBOX"]

        count = 0
        page_token = None
        # Hard cap pages so worst-case doesn’t explode; you only need a small badge number.
        MAX_PAGES = 4

        for _ in range(MAX_PAGES):
            resp = svc.users().messages().list(
                userId="me",
                q=q,
                labelIds=label_ids,
                maxResults=100,
                pageToken=page_token
            ).execute() or {}

            count += len(resp.get("messages", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return {"count": count, "status": "ok"}
    except Exception as e:
        # Keep it resilient; don't break the dashboard over Gmail hiccups.
        return {"count": 0, "status": "error", "detail": str(e)}

# ---------- send ----------
def _mime(to: str, subject: str, body_html: str) -> str:
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    msg.attach(MIMEText(body_html or "", "html"))
    import base64 as _b64
    return _b64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

@router.post("/reply")
def reply(payload: Dict, request: Request):
    """Send email using the signed-in user's Gmail."""
    for key in ("to", "subject", "body"):
        if not payload.get(key):
            raise HTTPException(status_code=400, detail=f"Missing {key}")

    user_email = _require_user_email(request)
    svc = _service_for(user_email)
    if not svc:
        raise HTTPException(status_code=400, detail="No Gmail token found for logged-in user")

    try:
        raw = _mime(payload["to"], payload["subject"], payload["body"])
        sent = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"status": "ok", "id": sent.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
