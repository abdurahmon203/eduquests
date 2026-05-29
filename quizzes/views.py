from django.shortcuts import render, get_object_or_404, redirect
from levels.models import Level
from .models import Question


def quiz_view(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    questions = level.questions.all()

    if request.method == "POST":
        score = 0
        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")
            if user_answer == question.correct_answer:
                score += 10
        request.session["score"] = score
        return redirect("quiz_result", level_id=level.id)

    context = {
        "level": level,
        "questions": questions,
    }

    return render(request, "quizzes/quiz.html", context)


def quiz_result(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    score = request.session.get("score", 0)

    return render(request, "quizzes/result.html", {"level": level, "score": score})
