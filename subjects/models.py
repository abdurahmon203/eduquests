from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="subjects/")
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        ordering = ["name"]

    def __str__(self):
        return self.name
