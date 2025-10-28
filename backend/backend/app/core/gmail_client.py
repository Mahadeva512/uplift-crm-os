import os, base64, email, mimetypes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Gmail Client Helper
# ---------------------------------------------------------------------------
class GmailClient:
    def __init__(self, user_email: str):
        """
        Gmail client wrapper for the logged-in CRM user's Gmail.
        Automatically locates token in the portable TOKEN_DIR.
        """
        self.user_email = user_email

        # Cloud/local portable token path
        TOKEN_DIR = os.getenv(
            "GMAIL_TOKEN_DIR",
            r"C:\Users\Mahadeva Swamy\Desktop\uplift-crm-vpro\backend\app\routers\credentials"
        )

        # Try both filename styles
        normal_path = os.path.join(TOKEN_DIR, f"{user_email}.json")
        prefixed_path = os.path.join(TOKEN_DIR, f"token_{user_email}.json")

        if os.path.exists(normal_path):
            token_path = normal_path
        elif os.path.exists(prefixed_path):
            token_path = prefixed_path
        else:
            raise HTTPException(
                status_code=400,
                detail=f"No Gmail token found for {user_email}. "
                       f"Tried:\n{normal_path}\n{prefixed_path}\n"
                       "Please connect Gmail first."
            )

        creds = Credentials.from_authorized_user_file(token_path, ["https://mail.google.com/"])
        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # -----------------------------------------------------------------------
    # Send or Reply
    # -----------------------------------------------------------------------
    async def send_email(self, to, subject, body, threadId=None, attachments=None):
        """
        Send or reply to an email. Keeps threading if threadId is provided.
        """
        message = email.message.EmailMessage()
        message.set_content(body or "")
        message["To"] = to
        message["Subject"] = subject
        message["From"] = self.user_email

        # Thread linking (critical)
        if threadId:
            try:
                thread = self.service.users().threads().get(userId="me", id=threadId).execute()
                parent_headers = {h["name"]: h["value"] for h in thread["messages"][0]["payload"]["headers"]}
                parent_mid = parent_headers.get("Message-ID")
                if parent_mid:
                    message["In-Reply-To"] = parent_mid
                    message["References"] = parent_mid
            except Exception as e:
                print("⚠️ Warning: could not fetch thread for linking:", e)

        # Attachments
        if attachments:
            for file in attachments:
                try:
                    content = await file.read()
                finally:
                    await file.close()
                mime_type, _ = mimetypes.guess_type(file.filename)
                maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
                message.add_attachment(content, maintype=maintype, subtype=subtype, filename=file.filename)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_dict = {"raw": raw}
        if threadId:
            body_dict["threadId"] = threadId  # ensures Gmail threads this message

        try:
            sent = self.service.users().messages().send(userId="me", body=body_dict).execute()
            return {"id": sent.get("id"), "threadId": sent.get("threadId")}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gmail send error: {e}")

    # -----------------------------------------------------------------------
    # Mark Thread Read / Unread
    # -----------------------------------------------------------------------
    def mark_thread(self, threadId, unread=False):
        try:
            mods = {"addLabelIds": ["UNREAD"]} if unread else {"removeLabelIds": ["UNREAD"]}
            self.service.users().threads().modify(userId="me", id=threadId, body=mods).execute()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mark thread failed: {e}")

    # -----------------------------------------------------------------------
    # Fetch Messages for a Lead
    # -----------------------------------------------------------------------
    def get_messages(self, lead_email):
        """
        Fetch latest 30 messages between CRM user and lead.
        """
        try:
            results = self.service.users().messages().list(
                userId="me", q=f"from:{lead_email} OR to:{lead_email}", maxResults=30
            ).execute()
            messages = []
            for m in results.get("messages", []):
                full = self.service.users().messages().get(userId="me", id=m["id"]).execute()
                messages.append(full)
            return messages
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Message fetch error: {e}")
