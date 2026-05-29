from django.shortcuts import render
from .models import Subject


def subject_list(request):
    subjects = Subject.objects.all()

    context = {"subjects": subjects}

    return render(request, "subjects/subject_list.html", context)
