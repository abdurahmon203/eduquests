from django.shortcuts import render, get_object_or_404
from subjects.models import Subject


def level_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    levels = subject.levels.all()
    context = {
        "subject": subject,
        "levels": levels,
    }

    return render(request, "levels/level_list.html", context)
