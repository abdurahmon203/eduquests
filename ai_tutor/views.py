import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from quizzes.models import Question

from .models import TutorQuestion, TutorResponse
from .services.gemini_service import (
    generate_tutor_response,
    is_api_configured,
    resolve_api_key,
)

logger = logging.getLogger(__name__)


def _parse_ask_payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return None
    return {
        "question": request.POST.get("question", ""),
        "subject": request.POST.get("subject", ""),
        "level": request.POST.get("level", ""),
        "quiz_question_id": request.POST.get("quiz_question_id"),
    }


@login_required
@require_GET
def chat_page(request):
    history = (
        TutorQuestion.objects.filter(user=request.user)
        .select_related("ai_response")
        .order_by("-created_at")[:30]
    )
    messages = []
    for item in reversed(list(history)):
        messages.append(
            {
                "role": "user",
                "content": item.question_text,
                "created_at": item.created_at.isoformat(),
            }
        )
        if hasattr(item, "ai_response"):
            messages.append(
                {
                    "role": "assistant",
                    "content": item.ai_response.answer_text,
                    "created_at": item.ai_response.created_at.isoformat(),
                }
            )

    configured = is_api_configured(session=request.session)
    has_session_key = bool((request.session.get("gemini_api_key") or "").strip())

    return render(
        request,
        "ai_tutor/chat.html",
        {
            "chat_messages": messages,
            "ai_configured": configured,
            "ai_has_session_key": has_session_key,
            "ai_default_model": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
        },
    )


@login_required
@require_GET
def ai_status(request):
    configured = is_api_configured(session=request.session)
    return JsonResponse(
        {
            "configured": configured,
            "has_session_key": bool((request.session.get("gemini_api_key") or "").strip()),
            "model": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
        }
    )


@login_required
@require_POST
def ai_settings(request):
    """Save Gemini API key in session (per browser, not stored in DB)."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    action = (payload.get("action") or "save").strip().lower()
    if action == "clear":
        request.session.pop("gemini_api_key", None)
        request.session.modified = True
        return JsonResponse({"ok": True, "configured": is_api_configured(session=request.session)})

    api_key = (payload.get("api_key") or "").strip()
    if not api_key:
        return JsonResponse({"error": "API key is required."}, status=400)

    request.session["gemini_api_key"] = api_key
    request.session.modified = True

    if payload.get("test"):
        try:
            answer, _source = generate_tutor_response(
                "What is 2+2? Reply in one short sentence.",
                session=request.session,
                allow_offline_fallback=False,
            )
            return JsonResponse(
                {
                    "ok": True,
                    "configured": True,
                    "test_answer": answer[:200],
                }
            )
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "configured": True})


@login_required
@require_POST
def ask(request):
    payload = _parse_ask_payload(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    question_text = (payload.get("question") or "").strip()
    subject = (payload.get("subject") or "").strip()
    level = (payload.get("level") or "").strip()

    if not question_text:
        return JsonResponse({"error": "Question is required."}, status=400)

    quiz_question = None
    quiz_question_id = payload.get("quiz_question_id")
    if quiz_question_id:
        quiz_question = Question.objects.filter(pk=quiz_question_id).first()

    tutor_question = TutorQuestion.objects.create(
        user=request.user,
        question_text=question_text,
        subject=subject,
        level=level,
        quiz_question=quiz_question,
    )

    try:
        answer, source = generate_tutor_response(
            question_text,
            subject=subject,
            level=level,
            session=request.session,
            allow_offline_fallback=True,
        )
    except ValueError as exc:
        logger.exception("AI tutor ValueError")
        return JsonResponse({"error": str(exc)}, status=503)
    except Exception as exc:
        logger.exception("AI tutor error: %s", exc)
        return JsonResponse(
            {
                "error": (
                    "AI tutor error. Open settings and paste a valid Gemini API key from "
                    "https://aistudio.google.com/apikey"
                )
            },
            status=502,
        )

    TutorResponse.objects.create(
        tutor_question=tutor_question,
        answer_text=answer,
    )

    return JsonResponse({"answer": answer, "source": source})
