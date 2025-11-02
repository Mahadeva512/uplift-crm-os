import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db.session import get_db
from app.models.activities import Activity

load_dotenv()
router = APIRouter(prefix="/ai", tags=["AI & Copilot"])

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
HF_API_KEY = os.getenv("HF_API_KEY")
HF_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


# ---------------------------------------------------------------------
# SUMMARIZE ACTIVITY
# ---------------------------------------------------------------------
@router.post("/summarize/{activity_id}")
async def summarize_activity(activity_id: str, db: Session = Depends(get_db)):
    """Summarizes a CRM activity in one clean, professional line."""

    act = db.query(Activity).get(activity_id)
    if not act:
        raise HTTPException(404, "Activity not found")

    desc = (act.description or "").strip()
    context = f"{act.type or 'Activity'} - {desc}"[:800]
    summary = None

    # --- 1️⃣ Primary: OpenRouter GPT-4o-mini
    if OPENROUTER_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://upliftcrm.ai",
                "X-Title": "Uplift CRM AI Copilot",
                "Content-Type": "application/json",
            }
            prompt = (
                f"Activity: {context}\n"
                "Summarize this for a CRM timeline in one short, factual, professional sentence. "
                "Avoid generic, global or marketing language."
            )
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 60,
                "temperature": 0.3,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if res.status_code == 200:
                summary = (
                    res.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
        except Exception as e:
            print("⚠️ OpenRouter summarization fallback:", e)

    # --- 2️⃣ Secondary: Hugging Face Flan-T5
    if not summary and HF_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
            payload = {"inputs": f"Summarize this CRM activity clearly: {context}"}
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(HF_URL, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and data:
                    summary = data[0].get("generated_text") or data[0].get("summary_text", "")
        except Exception as e:
            print("⚠️ Hugging Face summarization failed:", e)

    # --- 3️⃣ Fallback: Local Clean Summary
    if not summary:
        summary = desc or "(no description)"
    summary = (
        summary.replace("\n", " ")
        .replace("U.S.", "")
        .replace("Australia", "")
        .replace("New Zealand", "")
        .strip()
    )
    if len(summary) > 150:
        summary = summary[:147] + "..."

    # --- 4️⃣ Simple sentiment
    sentiment = "Neutral"
    low = summary.lower()
    if any(w in low for w in ["confirm", "success", "approved", "completed", "received", "thank"]):
        sentiment = "Positive"
    elif any(w in low for w in ["cancel", "delay", "angry", "problem", "lost", "not interested"]):
        sentiment = "Negative"

    # --- 5️⃣ Save
    act.ai_summary = summary
    act.ai_sentiment = sentiment
    act.meta = act.meta or {}
    act.meta["ai_summary"] = summary
    db.commit()

    return {"summary": summary, "sentiment": sentiment}


# ---------------------------------------------------------------------
# NEXT STEP SUGGESTION
# ---------------------------------------------------------------------
@router.post("/next-step/{activity_id}")
async def suggest_next_step(activity_id: str, db: Session = Depends(get_db)):
    """Suggests next logical CRM action."""

    act = db.query(Activity).get(activity_id)
    if not act:
        raise HTTPException(404, "Activity not found")

    desc = (act.description or "").strip().lower()
    suggestion = "Review activity and plan next logical step."

    # --- Rule-based fallback
    if "quotation" in desc:
        suggestion = "Follow up to confirm quotation and get approval."
    elif "payment" in desc:
        suggestion = "Remind client for pending payment and share receipt."
    elif "visit" in desc:
        suggestion = "Schedule on-site visit and confirm meeting time."
    elif "call" in desc:
        suggestion = "Call client to update status or confirm appointment."
    elif "meeting" in desc:
        suggestion = "Prepare summary notes and follow-up with client."

    # --- AI-powered (OpenRouter)
    if OPENROUTER_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://upliftcrm.ai",
                "X-Title": "Uplift CRM AI Copilot",
                "Content-Type": "application/json",
            }
            prompt = (
                f"Activity: {desc}\n"
                "Suggest one short next step for a CRM user — practical, task-based, clear."
            )
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 60,
                "temperature": 0.4,
            }
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if res.status_code == 200:
                ai_text = (
                    res.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if ai_text and len(ai_text) > 10:
                    suggestion = ai_text
        except Exception as e:
            print("⚠️ OpenRouter next-step fallback:", e)

    act.meta = act.meta or {}
    act.meta["ai_next_step"] = suggestion
    db.commit()

    return {"suggestion": suggestion}


# ---------------------------------------------------------------------
# INSIGHTS
# ---------------------------------------------------------------------
@router.get("/insights")
async def get_ai_insights(days: int = 7, db: Session = Depends(get_db)):
    """Returns aggregated AI metrics for dashboard."""
    try:
        total = db.query(Activity).count()
        pending = db.query(Activity).filter(Activity.status == "Pending").count()
        completed = db.query(Activity).filter(Activity.status == "Completed").count()

        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for act in db.query(Activity).all():
            if hasattr(act, "ai_sentiment") and act.ai_sentiment in sentiment_counts:
                sentiment_counts[act.ai_sentiment] += 1

        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "sentiment": sentiment_counts,
        }
    except Exception as e:
        print("⚠️ AI Insights failed:", e)
        return {"total": 0, "pending": 0, "completed": 0, "sentiment": {}}
