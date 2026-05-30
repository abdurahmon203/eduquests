from django.db import models
from subjects.models import Subject
import re
from urllib.parse import urlparse, parse_qs


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

    @property
    def youtube_video_id(self):
        url = (self.video_url or "").strip()
    
        if "youtu.be/" in url:
            return url.split("/")[-1].split("?")[0]
    
        if "/embed/" in url:
            return url.split("/embed/")[1].split("?")[0]
    
        if "youtube.com" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if video_id:
                return video_id
    
        match = re.search(r"([a-zA-Z0-9_-]{11})", url)
        return match.group(1) if match else ""