import json
import os
import re
import urllib.error
import urllib.request

REFUSAL_MESSAGE = (
    "I can't give direct answers, but I can explain how to solve it and help you understand."
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

SYSTEM_PROMPT = """You are EduQuests AI Tutor — a warm, patient personal teacher inside a gamified learning platform.
RULES (never break these):
1. Teach concepts; do NOT give direct answers to quiz, test, exam, or homework questions.
2. If the student asks for a direct/correct answer to pass a test, refuse politely and offer to teach the concept instead.
3. Stay educational, encouraging, and age-appropriate.
4. Never reveal or guess correct multiple-choice letters (A/B/C/D) for assessment questions.

RESPONSE FORMAT — always use exactly these three sections with markdown bold headers:

**Simple explanation**
(2-4 short sentences, plain language)

**Example**
(One concrete, easy example)

**Now try**
(One follow-up question that checks understanding — not the answer)

Keep total response under 200 words unless the topic truly needs more. Be friendly, not robotic."""


def is_cheating_request(question: str) -> bool:
    text = question.lower()
    for pattern in CHEATING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_api_key():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your environment or .env file."
        )
    return api_key


def generate_tutor_response(
    question: str,
    subject: str = "",
    level: str = "",
) -> str:
    if is_cheating_request(question):
        return REFUSAL_MESSAGE

    context_parts = []
    if subject:
        context_parts.append(f"Subject: {subject}")
    if level:
        context_parts.append(f"Level: {level}")
    context = "\n".join(context_parts)

    user_content = question
    if context:
        user_content = f"{context}\n\nStudent question:\n{question}"

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }

    req = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Groq API error ({exc.code}): {body[:200]}") from exc

    answer = data["choices"][0]["message"]["content"]
    if not answer or not answer.strip():
        raise ValueError("Empty response from Groq API.")

    return _ensure_response_structure(answer.strip())


def _ensure_response_structure(text: str) -> str:
    """Gently normalize so all three sections exist."""
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
