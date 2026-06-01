from django.urls import path

from . import views

urlpatterns = [
    path("ai-tutor/", views.chat_page, name="ai_tutor_chat"),
    path("ai/ask/", views.ask, name="ai_ask"),
    path("ai/status/", views.ai_status, name="ai_status"),
    path("ai/settings/", views.ai_settings, name="ai_settings"),
]
