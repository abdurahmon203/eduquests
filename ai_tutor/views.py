import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from quizzes.models import Question

from .models import TutorQuestion, TutorResponse
from .services.groq_service import generate_tutor_response


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

    return render(
        request,
        "ai_tutor/chat.html",
        {"chat_messages": messages},
    )


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
        answer = generate_tutor_response(
            question_text,
            subject=subject,
            level=level,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    except Exception:
        return JsonResponse(
            {"error": "AI tutor is temporarily unavailable. Please try again."},
            status=502,
        )

    TutorResponse.objects.create(
        tutor_question=tutor_question,
        answer_text=answer,
    )

    return JsonResponse({"answer": answer})
