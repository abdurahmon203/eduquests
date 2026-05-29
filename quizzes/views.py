from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from levels.models import Level
from .models import Question
from gamification.models import UserProgress
from django.utils import timezone


@login_required
def quiz_view(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    questions = Question.objects.filter(level=level)
    if request.method == "POST":
        score = 0
        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")

            if user_answer == question.correct_answer:
                score += 10
        xp = score
        is_completed = False
        if score >= 50:
            xp += 50
            is_completed = True
            
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            level=level,
        )
        was_completed = progress.is_completed
        progress.score = score
        progress.xp_earned = max(progress.xp_earned, xp)
        progress.attempts += 1
        progress.is_completed = is_completed
        if is_completed and not progress.completed_at:
            progress.completed_at = timezone.now()
        progress.save()

        # Update user's profile score if newly completed
        if is_completed and not was_completed:
            request.user.score += xp
            request.user.save()

        request.session["score"] = score
        return redirect("quiz_result", level_id=level.id)

    return render(
        request,
        "quizzes/quiz.html",
        {
            "level": level,
            "questions": questions,
        },
    )


@login_required
def quiz_result(request, level_id):
    level = get_object_or_404(Level, id=level_id)

    progress = UserProgress.objects.filter(user=request.user, level=level).first()

    score = request.session.get("score", 0)

    return render(
        request,
        "quizzes/result.html",
        {
            "level": level,
            "score": score,
            "progress": progress,
        },
    )
