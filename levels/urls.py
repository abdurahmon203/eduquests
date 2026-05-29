from django.urls import path
from .views import level_list, learn_vidios

urlpatterns = [
    path("<int:subject_id>/", level_list, name="level_list"),
    path("learn/", learn_vidios, name="learn_vidios")
]
