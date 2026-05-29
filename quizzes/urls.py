from django.urls import path
from . import views

urlpatterns = [
    path("<int:level_id>/", views.quiz_view, name="quiz"),
    path("<int:level_id>/result/", views.quiz_result, name="quiz_result"),
]
