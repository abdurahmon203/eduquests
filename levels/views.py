from django.shortcuts import render, get_object_or_404
from subjects.models import Subject
from gamification.models import UserProgress


def level_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    levels = subject.levels.all()
    
    completed_level_ids = []
    if request.user.is_authenticated:
        completed_level_ids = list(
            UserProgress.objects.filter(
                user=request.user,
                level__subject=subject,
                is_completed=True
            ).values_list("level_id", flat=True)
        )
        
    context = {
        "subject": subject,
        "levels": levels,
        "completed_level_ids": completed_level_ids,
    }

    return render(request, "levels/level_list.html", context)
