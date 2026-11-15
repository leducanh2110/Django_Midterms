from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm


@require_http_methods(["GET"])
def home(request):
    destination = "accounts:dashboard" if request.user.is_authenticated else "accounts:login"
    return redirect(destination)


@never_cache
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        # UserCreationForm.save() hashes the password and saves through the ORM.
        form.save()
        messages.success(request, "Account created! Sign in with your new credentials.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


@never_cache
@login_required
def dashboard(request):
    return render(request, "accounts/dashboard.html")
