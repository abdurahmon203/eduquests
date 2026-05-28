from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
