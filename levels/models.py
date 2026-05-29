from django.db import models
from subjects.models import Subject


class Level(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="levels"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    level_number = models.PositiveIntegerField()
    video_url = models.URLField(blank=True, null=True)
    required_score = models.PositiveIntegerField(default=0)
    xp_reward = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Level"
        verbose_name_plural = "Levels"
        ordering = ["subject", "level_number"]
        unique_together = ("subject", "level_number")

    def __str__(self):
        return f"{self.subject.name} - Level {self.level_number}"
