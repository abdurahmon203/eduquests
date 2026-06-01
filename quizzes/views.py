from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from levels.models import Level
from gamification.models import UserProgress
from gamification.xp import sync_user_score
from django.utils import timezone

from .utils import (
    clear_attempt_questions,
    load_attempt_questions,
    parse_question_count,
    select_questions_for_attempt,
    store_attempt_questions,
)


def _grade_quiz(questions, post_data):
    score = 0
    for question in questions:
        user_answer = post_data.get(f"question_{question.id}")
        if user_answer == question.correct_answer:
            score += 10
    return score


@login_required
def quiz_view(request, level_id):
    level = get_object_or_404(Level, id=level_id)

    if request.method == "POST":
        questions = load_attempt_questions(request.session, level)
        if not questions:
            return redirect("quiz", level_id=level.id)

        score = _grade_quiz(questions, request.POST)
        max_score = len(questions) * 10
        pass_threshold = max_score * 0.5
        xp = score
        is_completed = score >= pass_threshold
        if is_completed:
            xp += 50

        progress, _created = UserProgress.objects.get_or_create(
            user=request.user,
            level=level,
        )
        progress.score = score
        progress.xp_earned = max(progress.xp_earned, xp)
        progress.attempts += 1
        progress.is_completed = progress.is_completed or is_completed
        if is_completed and not progress.completed_at:
            progress.completed_at = timezone.now()
        progress.save()
        sync_user_score(request.user)

        clear_attempt_questions(request.session, level.id)
        request.session["score"] = score
        request.session["quiz_max_score"] = max_score
        return redirect("quiz_result", level_id=level.id)

    count = parse_question_count(request)
    questions = select_questions_for_attempt(
        level,
        count=count,
        session=request.session,
    )
    store_attempt_questions(request.session, level.id, questions)

    total_in_level = level.questions.count()

    return render(
        request,
        "quizzes/quiz.html",
        {
            "level": level,
            "questions": questions,
            "total_in_level": total_in_level,
            "showing_count": len(questions),
        },
    )


@login_required
def quiz_result(request, level_id):
    level = get_object_or_404(Level, id=level_id)

    progress = UserProgress.objects.filter(user=request.user, level=level).first()

    score = request.session.get("score", 0)
    max_score = request.session.get("quiz_max_score", 50)
    pass_threshold = int(max_score * 0.5)

    return render(
        request,
        "quizzes/result.html",
        {
            "level": level,
            "score": score,
            "max_score": max_score,
            "pass_threshold": pass_threshold,
            "passed": score >= pass_threshold,
            "progress": progress,
        },
    )
