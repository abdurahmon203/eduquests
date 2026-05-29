from django.db import models
from django.conf import settings
from levels.models import Level


class UserProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress"
    )
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="progress")
    score = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(
        default=0,
        help_text="Total XP earned for this level (best attempt).",
    )
    attempts = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("user", "level")

    def __str__(self):
        return f"{self.user.email} - {self.level.title}"
