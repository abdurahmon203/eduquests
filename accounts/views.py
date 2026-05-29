import random
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from gamification.xp import get_user_completed_levels, get_user_total_xp, sync_user_score

from .models import User
from .forms import (
    ContactForm,
    ProfileForm,
    PasswordChangeForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)

OTP_EXPIRY = timedelta(minutes=1, seconds=30)


def _send_otp_email(email, otp, subject="EduQuests Verification Code"):
    send_mail(
        subject,
        f"Your verification code is: {otp}",
        None,
        [email],
        fail_silently=False,
    )


def _otp_expired(user):
    if not user.otp_created_at:
        return True
    return timezone.now() > user.otp_created_at + OTP_EXPIRY


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

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("register")

        otp = str(random.randint(100000, 999999))

        try:
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
            _send_otp_email(email, otp)
        except Exception:
            messages.error(request, "Could not create account. Please try again.")
            return redirect("register")

        request.session["email"] = email
        return redirect("verify")

    return render(request, "accounts/register.html")


def verify_view(request):
    email = request.session.get("email")
    if not email:
        return redirect("register")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    if request.method == "POST":
        code = request.POST.get("code")
        if _otp_expired(user):
            messages.error(request, "Code expired. Please register again.")
            return redirect("register")

        if code == user.otp_code:
            user.is_verified = True
            user.is_active = True
            user.otp_code = None
            user.otp_created_at = None
            user.save()
            login(request, user)
            messages.success(request, "Email verified! Welcome to EduQuests.")
            return redirect("home")
        messages.error(request, "Invalid code")

    return render(request, "accounts/verify.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid credentials")
        elif not user.is_verified or not user.is_active:
            messages.error(
                request,
                "Please verify your email before logging in. Check your inbox for the code.",
            )
        else:
            login(request, user)
            next_url = request.GET.get("next") or "home"
            return redirect(next_url)

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.success(
                    request,
                    "If an account exists for that email, we sent a reset code.",
                )
                return redirect("reset_password")

            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.save(update_fields=["otp_code", "otp_created_at"])

            try:
                _send_otp_email(
                    email,
                    otp,
                    subject="EduQuests Password Reset Code",
                )
            except Exception:
                messages.error(request, "Could not send email. Please try again later.")
                return redirect("forgot_password")

            request.session["reset_email"] = email
            messages.success(request, "Reset code sent! Check your email.")
            return redirect("reset_password")

        messages.error(request, "Please enter a valid email address.")
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form})


def reset_password_view(request):
    email = request.session.get("reset_email")
    if not email:
        return redirect("forgot_password")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "Session expired. Please request a new code.")
        return redirect("forgot_password")

    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            if _otp_expired(user):
                messages.error(request, "Code expired. Please request a new one.")
                return redirect("forgot_password")

            if form.cleaned_data["code"] != user.otp_code:
                messages.error(request, "Invalid verification code")
            else:
                user.set_password(form.cleaned_data["new_password"])
                user.otp_code = None
                user.otp_created_at = None
                user.is_active = True
                user.is_verified = True
                user.save()
                del request.session["reset_email"]
                messages.success(request, "Password updated! You can log in now.")
                return redirect("login")
    else:
        form = ResetPasswordForm()

    return render(request, "accounts/reset_password.html", {"form": form, "email": email})


@login_required
def profile_view(request):
    user = request.user
    profile_form = ProfileForm(instance=user)
    password_form = PasswordChangeForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "profile":
            profile_form = ProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                email = profile_form.cleaned_data["email"]
                username = profile_form.cleaned_data["username"]
                if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                    messages.error(request, "That email is already in use.")
                elif User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    messages.error(request, "That username is already taken.")
                else:
                    profile_form.save()
                    messages.success(request, "Profile updated successfully.")
                    return redirect("profile")
            else:
                messages.error(request, "Please fix the errors in your profile form.")

        elif action == "password":
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                if not user.check_password(password_form.cleaned_data["current_password"]):
                    messages.error(request, "Current password is incorrect.")
                else:
                    user.set_password(password_form.cleaned_data["new_password"])
                    user.save()
                    login(request, user)
                    messages.success(request, "Password changed successfully.")
                    return redirect("profile")
            else:
                for err in password_form.non_field_errors():
                    messages.error(request, err)

    sync_user_score(user)
    total_xp = get_user_total_xp(user)
    completed_levels = get_user_completed_levels(user)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "total_xp": total_xp,
            "completed_levels": completed_levels,
        },
    )


def home_view(request):
    return render(request, "home.html")


def about_view(request):
    return render(request, "about.html")


def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Your message has been sent successfully! We will get back to you shortly.",
            )
            return redirect("contact")
        messages.error(request, "There was an error in your submission. Please check the fields below.")
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})
