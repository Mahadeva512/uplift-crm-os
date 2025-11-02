from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64, email, mimetypes, os

router = APIRouter(prefix="/integrations/gmail", tags=["Gmail"])

SCOPES = ["https://mail.google.com/"]

# Portable token directory (cloud-ready)
TOKEN_DIR = os.getenv(
    "GMAIL_TOKEN_DIR",
    r"C:\Users\Mahadeva Swamy\Desktop\uplift-crm-vpro\backend\app\routers\credentials",
)

def _token_path_for(user_email: str) -> str:
    """Support both token_<email>.json and <email>.json (your app uses the token_ pattern)."""
    pref = os.path.join(TOKEN_DIR, f"token_{user_email}.json")
    plain = os.path.join(TOKEN_DIR, f"{user_email}.json")
    if os.path.exists(pref):
        return pref
    if os.path.exists(plain):
        return plain
    return pref  # default path shown in error

def _get_service(user_email: str):
    tpath = _token_path_for(user_email)
    if not os.path.exists(tpath):
        raise HTTPException(
            status_code=400,
            detail=f"No Gmail token for {user_email} (expected {tpath}). Connect Gmail first.",
        )
    creds = Credentials.from_authorized_user_file(tpath, SCOPES)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def _header_map(msg):
    return {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

# ------------------------------ Messages list for a lead ------------------------------ #
@router.get("/messages/{lead_email}")
def list_messages(lead_email: str, user_email: str):
    """
    Return messages (latest first) between the logged-in user (user_email)
    and the given lead_email.
    """
    svc = _get_service(user_email)
    q = f"to:{lead_email} OR from:{lead_email}"

    try:
        res = svc.users().messages().list(userId="me", q=q, maxResults=30).execute()
        items = []
        for itm in (res.get("messages") or []):
            full = svc.users().messages().get(userId="me", id=itm["id"], format="full").execute()
            items.append(full)
        items.sort(key=lambda m: int(m.get("internalDate", "0")), reverse=True)
        return {"messages": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail fetch error: {e}")

# ------------------------------ Mark thread read/unread ------------------------------ #
@router.post("/thread/mark")
def mark_thread(user_email: str, threadId: str, unread: bool = False):
    svc = _get_service(user_email)
    try:
        mods = {"addLabelIds": ["UNREAD"]} if unread else {"removeLabelIds": ["UNREAD"]}
        svc.users().threads().modify(userId="me", id=threadId, body=mods).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mark thread failed: {e}")

# ------------------------------ Send / Reply ------------------------------ #
@router.post("/reply")
async def send_reply(
    user_email: str,
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    threadId: Optional[str] = Form(None),
    attachments: Optional[List[UploadFile]] = File(None),
):
    """
    Send a new email or reply in the *same thread*.
    - Auth account is the logged-in CRM user (user_email)
    - 'to' is the lead email
    - If threadId is provided, we thread using Gmail's threadId + In-Reply-To/References.
    """
    svc = _get_service(user_email)

    try:
        # Build RFC822 message
        msg = email.message.EmailMessage()
        msg["From"] = user_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body or "")

        # Thread linking (fetch any msg to get Message-ID for In-Reply-To / References)
        if threadId:
            try:
                thread = svc.users().threads().get(userId="me", id=threadId, format="full").execute()
                first_msg = (thread.get("messages") or [None])[0]
                if first_msg:
                    headers = _header_map(first_msg)
                    parent_mid = headers.get("Message-ID")
                    if parent_mid:
                        msg["In-Reply-To"] = parent_mid
                        msg["References"] = parent_mid
            except Exception as e:
                print("⚠️ Could not fetch parent for thread linking:", e)

        # Attachments
        if attachments:
            for up in attachments:
                try:
                    raw = await up.read()
                finally:
                    await up.close()
                mime_type, _ = mimetypes.guess_type(up.filename)
                maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
                msg.add_attachment(raw, maintype=maintype, subtype=subtype, filename=up.filename)

        # Encode & send
        raw_str = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload = {"raw": raw_str}
        if threadId:
            payload["threadId"] = threadId

        sent = svc.users().messages().send(userId="me", body=payload).execute()
        return {"status": "sent", "id": sent.get("id"), "threadId": sent.get("threadId")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail send error: {e}")

# ------------------------------ Optional health check ------------------------------ #
@router.get("/token/check")
def token_check(user_email: str):
    return {"exists": os.path.exists(_token_path_for(user_email))}
