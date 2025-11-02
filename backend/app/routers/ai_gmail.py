from fastapi import APIRouter, HTTPException
from typing import List, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import httpx, base64, os, re

router = APIRouter(prefix="/ai/gmail", tags=["AI Gmail"])

SCOPES = ["https://mail.google.com/"]
HF_API_KEY = os.getenv("HF_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")  # change if you prefer

# Portable token directory (same contract as gmail.py)
TOKEN_DIR = os.getenv(
    "GMAIL_TOKEN_DIR",
    r"C:\Users\Mahadeva Swamy\Desktop\uplift-crm-vpro\backend\app\routers\credentials",
)

# ------------------------------ Helpers ------------------------------ #
def _token_path_for(user_email: str) -> str:
    """Return best-match token path, supporting both token_<email>.json and <email>.json."""
    pref = os.path.join(TOKEN_DIR, f"token_{user_email}.json")
    plain = os.path.join(TOKEN_DIR, f"{user_email}.json")
    if os.path.exists(pref):
        return pref
    if os.path.exists(plain):
        return plain
    # if neither exists, prefer to look for your convention first in the error message
    return pref

def _get_service(user_email: str):
    tpath = _token_path_for(user_email)
    if not os.path.exists(tpath):
        # Return a friendly error payload (UI shows banner) instead of throwing 4xx to browser
        raise HTTPException(status_code=400, detail=f"No Gmail token: {tpath}")
    creds = Credentials.from_authorized_user_file(tpath, SCOPES)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def _clean_html(raw_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw_html or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _extract_text_from_message(msg) -> str:
    payload = msg.get("payload", {})
    # multipart
    for part in payload.get("parts", []) or []:
        mt = part.get("mimeType")
        data = part.get("body", {}).get("data")
        if not data:
            continue
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
        if mt == "text/plain":
            return decoded
        if mt == "text/html":
            return _clean_html(decoded)
    # single-part
    body_data = payload.get("body", {}).get("data")
    if body_data:
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", "ignore")
        mt = payload.get("mimeType", "text/plain")
        return decoded if mt == "text/plain" else _clean_html(decoded)
    # fallback
    return msg.get("snippet", "")

# ------------------------------ Providers ------------------------------ #
async def _call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "Summary unavailable."
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {
        "model": OR_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 400,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    j = r.json()
    try:
        return j["choices"][0]["message"]["content"].strip()
    except Exception:
        return "Summary unavailable."

async def _call_hf(prompt: str) -> str:
    if not HF_API_KEY:
        return "Summary unavailable."
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
            headers=headers,
            json={"inputs": prompt},
        )
    j = r.json()
    if isinstance(j, list) and j and "summary_text" in j[0]:
        return j[0]["summary_text"]
    return "Summary unavailable."

# ------------------------------ Routes ------------------------------ #
@router.post("/summarize")
async def summarize(payload: Dict):
    """
    Summarize last 5 messages in a Gmail thread.

    Payload:
      - user_email : logged-in CRM user's Gmail (token owner)
      - thread_id  : Gmail threadId (or 'threadId')
      - subject    : optional, improves prompt
    """
    user_email = payload.get("user_email")
    thread_id = payload.get("thread_id") or payload.get("threadId")
    subject = payload.get("subject", "(no subject)")

    if not user_email or not thread_id:
        return {"summary": "Summary unavailable.", "error": f"Missing user_email or thread_id (got {payload})."}

    try:
        svc = _get_service(user_email)
    except HTTPException as e:
        return {"summary": "Summary unavailable.", "error": e.detail}

    try:
        thread = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
        msgs = (thread.get("messages") or [])
        msgs = msgs[-5:] if len(msgs) > 5 else msgs

        context = []
        for m in msgs:
            hdrs = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
            sender = hdrs.get("From", "Unknown")
            text = _extract_text_from_message(m)
            if text:
                context.append(f"From {sender}:\n{text}")

        if not context:
            return {"summary": "Summary unavailable.", "error": "No readable text found in thread."}

        prompt = (
            f"Summarize this professional email conversation about '{subject}' into 3–5 concise bullet points. "
            f"Focus on facts, decisions, asks, and next steps.\n\n"
            + "\n\n---\n\n".join(context)
        )

        summary = await (_call_openrouter(prompt) if OPENROUTER_API_KEY else _call_hf(prompt))
        return {"summary": summary}
    except Exception as e:
        return {"summary": "Summary unavailable.", "error": f"Gmail fetch error: {e}"}

@router.post("/suggest")
async def suggest(payload: Dict):
    """Tone-aware reply suggestion using OpenRouter (or a clean fallback)."""
    tone = payload.get("tone", "Neutral")
    subject = payload.get("subject", "(no subject)")
    last_messages: List[Dict] = payload.get("last_messages") or []

    thread_text = []
    for m in last_messages[-5:]:
        who = m.get("from", "Unknown")
        text = m.get("text") or m.get("snippet") or ""
        thread_text.append(f"{who}: {text}")
    thread_text = "\n".join(thread_text)[:10000]

    prompt = (
        f"You are a helpful business email assistant. "
        f"Write a {tone.lower()} professional reply to continue the email conversation about '{subject}'. "
        f"Be concise (120–180 words), include a warm opener, a short body, a clear call-to-action, and a polite closing.\n\n"
        f"Conversation so far:\n{thread_text}\n\nReply:\n"
    )

    try:
        if OPENROUTER_API_KEY:
            reply = await _call_openrouter(prompt)
            return {"reply": reply}
        # Fallback if no LLM key present
        return {
            "reply": (
                f"Thanks for your email regarding '{subject}'. "
                f"I’d love to continue this conversation—could you share a few suitable times for a quick call? "
                f"Happy to help further.\n\nBest regards,\n"
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
