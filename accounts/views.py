from django.shortcuts import render
import random
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from .models import User
from .forms import ContactForm


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


def verify_view(request):
    email = request.session.get("email")
    if not email:
        return redirect("register")
    user = User.objects.get(email=email)

    if request.method == "POST":
        code = request.POST.get("code")
        if timezone.now() > user.otp_created_at + timedelta(minutes=1, seconds=30):
            messages.error(request, "Code expired")
            return redirect("register")

        if code == user.otp_code:
            user.is_verified = True
            user.is_active = True
            user.otp_code = None
            user.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid code")

    return render(request, "accounts/verify.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def home_view(request):
    return render(request, "home.html")


def about_view(request):
    return render(request, "about.html")


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Your message has been sent successfully! We will get back to you shortly.")
            return redirect("contact")
        else:
            messages.error(request, "There was an error in your submission. Please check the fields below.")
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})
