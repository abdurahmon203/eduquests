from django.shortcuts import render
import random
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from .models import User


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register")
        otp = str(random.randint(100000, 999999))

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
            otp_code=otp,
            otp_created_at=timezone.now(),
            is_active=False,
        )

        send_mail(
            "EduQuests Verification Code",
            f"Your verification code is: {otp}",
            None,
            [email],
            fail_silently=False,
        )
        request.session["email"] = email

        return redirect("verify")

    return render(request, "accounts/register.html")
