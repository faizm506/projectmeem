from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from core import security

from .models import User


class StyledMixin:
    """Give every widget the MEEM input class."""

    def style(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " input").strip()


class SignUpForm(StyledMixin, UserCreationForm):
    role = forms.ChoiceField(choices=User.Role.choices, initial=User.Role.BUYER, label="I want to")

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [("buyer", "Shop on MEEM"), ("seller", "Sell on MEEM")]
        self.style()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(StyledMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()

    def clean(self):
        username = self.cleaned_data.get("username", "")
        if username and security.is_throttled(self.request, username):
            raise forms.ValidationError("Too many sign-in attempts. Please wait 15 minutes and try again.")
        return super().clean()
