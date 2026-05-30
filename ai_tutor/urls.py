from django.urls import path

from . import views

urlpatterns = [
    path("ai-tutor/", views.chat_page, name="ai_tutor_chat"),
    path("ai/ask/", views.ask, name="ai_ask"),
]
