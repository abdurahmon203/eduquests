from django import forms
from django.contrib.auth.password_validation import validate_password

from eduquests.i18n_strings import get_text

from .models import User


class ContactForm(forms.Form):
    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        t = lambda k: get_text(k, lang)
        self.fields["name"].label = t("contact.form_name")
        self.fields["email"].label = t("contact.form_email")
        self.fields["message"].label = t("contact.form_message")
        self.fields["name"].widget.attrs["placeholder"] = t("contact.form_name_ph")
        self.fields["email"].widget.attrs["placeholder"] = t("contact.form_email_ph")
        self.fields["message"].widget.attrs["placeholder"] = t("contact.form_message_ph")

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-input", "id": "contact_name"},
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-input", "id": "contact_email"},
        ),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-input", "id": "contact_message", "rows": 5},
        ),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "birth_date",
            "avatar",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Last name"}
            ),
            "username": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "you@example.com"}
            ),
            "birth_date": forms.DateInput(
                attrs={"class": "form-input", "type": "date"}
            ),
            "avatar": forms.FileInput(attrs={"class": "form-input form-file"}),
        }


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "••••••••"}
        ),
    )
    new_password = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "••••••••"}
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "••••••••"}
        ),
    )

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("New passwords do not match.")
        return cleaned


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "you@example.com",
            }
        ),
    )


class ResetPasswordForm(forms.Form):
    code = forms.CharField(
        label="Verification code",
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "6-digit code",
                "autocomplete": "one-time-code",
            }
        ),
    )
    new_password = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "••••••••"}
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "••••••••"}
        ),
    )

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
