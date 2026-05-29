from django.shortcuts import render, get_object_or_404, redirect
from levels.models import Level
from .models import Question


def quiz_view(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    questions = level.questions.all()
    context = {
        "level": level,
        "questions": questions,
    }

    return render(request, "quizzes/quiz.html", context)
