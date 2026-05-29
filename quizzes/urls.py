from django.urls import path
from . import views

urlpatterns = [
    path("<int:level_id>/", views.quiz_view, name="quiz"),
]
