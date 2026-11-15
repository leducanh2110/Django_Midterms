from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    """Add a required email to Django's password-validating registration form."""

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password2"].label = "Confirm password"
        self.fields["password2"].help_text = "Enter the same password again."
        placeholders = {
            "username": "Choose a username",
            "email": "you@example.com",
            "password1": "Create a strong password",
            "password2": "Repeat your password",
        }
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-input", "placeholder": placeholders[name]}
            )


class LoginForm(AuthenticationForm):
    """Keep Django's authentication behavior and add presentation attributes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-input", "placeholder": f"Enter your {name}"}
            )
