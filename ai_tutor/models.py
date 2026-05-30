from django.conf import settings
from django.db import models


class TutorQuestion(models.Model):
    """User questions to the AI tutor (separate from quiz Question model)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_questions",
    )
    question_text = models.TextField()
    subject = models.CharField(max_length=120, blank=True)
    level = models.CharField(max_length=120, blank=True)
    quiz_question = models.ForeignKey(
        "quizzes.Question",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tutor_sessions",
        help_text="Optional link to a quiz question for context only.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question_text[:60]


class TutorResponse(models.Model):
    """AI tutor reply — never modifies quiz Question.correct_answer."""

    tutor_question = models.OneToOneField(
        TutorQuestion,
        on_delete=models.CASCADE,
        related_name="ai_response",
    )
    answer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to #{self.tutor_question_id}"
