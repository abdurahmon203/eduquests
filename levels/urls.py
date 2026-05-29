from django.urls import path
from .views import level_list

urlpatterns = [
    path("<int:subject_id>/", level_list, name="level_list"),
]
