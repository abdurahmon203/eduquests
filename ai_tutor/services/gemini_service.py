import json
import logging
import os
import re
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE = (
    "I can't give direct answers, but I can help you understand the concept."
)

CHEATING_PATTERNS = [
    r"\bdirect\s+answer\b",
    r"\bexam\s+answer\b",
    r"\btest\s+answer\b",
    r"\bquiz\s+answer\b",
    r"\bquestion\s+model\b",
    r"\bgive\s+me\s+the\s+answer\b",
    r"\bwhat\s+is\s+the\s+correct\s+answer\b",
    r"\bmultiple\s+choice\s+answer\b",
    r"\bfinal\s+exam\b",
    r"\bcheat\b",
]

SYSTEM_PROMPT = """You are EduQuests AI Tutor — a warm, patient personal teacher.
RULES: Teach concepts. Never give direct quiz/test/exam answers or A/B/C/D letters.
Always respond with exactly these markdown sections:

**Simple explanation**
(2-4 short sentences)

**Example**
(one concrete example)

**Now try**
(one follow-up question, not the answer)

Keep under 200 words. Be friendly."""

# Models tried in order until one succeeds (2.0-flash free tier often has 0 quota).
MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def is_cheating_request(question: str) -> bool:
    text = question.lower()
    for pattern in CHEATING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def resolve_api_key(session=None):
    """Session key (from UI) overrides .env."""
    if session is not None:
        session_key = (session.get("gemini_api_key") or "").strip()
        if session_key:
            return session_key
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "No Gemini API key. Add GEMINI_API_KEY to .env or paste your key in AI Tutor settings."
        )
    return api_key


def is_api_configured(session=None):
    try:
        resolve_api_key(session=session)
        return True
    except ValueError:
        return False


def _models_to_try():
    preferred = (os.getenv("GEMINI_MODEL") or "").strip()
    models = []
    if preferred:
        models.append(preferred)
    for m in MODEL_FALLBACKS:
        if m not in models:
            models.append(m)
    return models


def _call_gemini_rest(api_key, model, user_content):
    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    candidates = data.get("candidates") or []
    if not candidates:
        block = (data.get("promptFeedback") or {}).get("blockReason")
        raise ValueError(block or "No response from Gemini.")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ValueError("Empty response from Gemini.")
    return text


def _offline_tutor_response(question: str, subject: str = "", level: str = "") -> str:
    """Works without API when quota/network fails."""
    topic = question.strip().rstrip("?").capitalize() or "This topic"
    ctx = subject or level or "your course"
    return (
        f"**Simple explanation**\n"
        f"{topic} is a key idea in {ctx}. Break it into small parts: what it is, "
        f"why it matters, and how you might see it in real life. "
        f"Review your notes or lesson video, then explain it aloud in your own words.\n\n"
        f"**Example**\n"
        f"Imagine you are teaching a friend who has never heard of {topic.lower()}. "
        f"Use one simple comparison from everyday life to make the idea click.\n\n"
        f"**Now try**\n"
        f"In one sentence, what is the main idea of {topic.lower()} — without copying a textbook?"
    )


def generate_tutor_response(
    question: str,
    subject: str = "",
    level: str = "",
    session=None,
    allow_offline_fallback: bool = True,
):
    """Returns (answer_text, source) where source is 'gemini' or 'offline'."""
    if is_cheating_request(question):
        return REFUSAL_MESSAGE, "gemini"

    context_parts = []
    if subject:
        context_parts.append(f"Subject: {subject}")
    if level:
        context_parts.append(f"Level: {level}")
    user_content = question
    if context_parts:
        user_content = "\n".join(context_parts) + f"\n\nStudent question:\n{question}"

    try:
        api_key = resolve_api_key(session=session)
    except ValueError:
        if allow_offline_fallback:
            return _offline_tutor_response(question, subject, level), "offline"
        raise

    errors = []
    for model in _models_to_try():
        try:
            text = _call_gemini_rest(api_key, model, user_content)
            logger.info("Gemini OK model=%s", model)
            return _ensure_response_structure(text), "gemini"
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                err = json.loads(body).get("error", {})
                msg = err.get("message", body[:200])
            except json.JSONDecodeError:
                msg = body[:200]
            errors.append(f"{model}: {exc.code} {msg}")
            logger.warning("Gemini fail model=%s code=%s", model, exc.code)
            if exc.code in (400, 401, 403):
                break
        except Exception as exc:
            errors.append(f"{model}: {exc}")
            logger.warning("Gemini fail model=%s err=%s", model, exc)

    if allow_offline_fallback:
        logger.warning("Gemini all models failed, using offline tutor. %s", errors[:2])
        return _offline_tutor_response(question, subject, level), "offline"

    raise ValueError(
        "Gemini API unavailable. Check your API key and billing at https://aistudio.google.com/apikey. "
        f"Details: {errors[0] if errors else 'unknown'}"
    )


def _ensure_response_structure(text: str) -> str:
    lower = text.lower()
    has_explanation = "simple explanation" in lower or "**simple" in lower
    has_example = "example" in lower
    has_try = "now try" in lower
    if has_explanation and has_example and has_try:
        return text
    return (
        f"**Simple explanation**\n{text}\n\n"
        "**Example**\nThink of a real-world case that matches this idea.\n\n"
        "**Now try**\nCan you explain this concept in your own words?"
    )
