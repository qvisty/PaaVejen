from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, SignupForm


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    user = request.user
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Din profil er opdateret.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=user)
    ratings = user.ratings_received.select_related("reviewer").order_by("-created_at")[:10]
    completed = user.bookings_as_driver.filter(status="completed").count() + \
        user.bookings_as_customer.filter(status="completed").count()
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "ratings": ratings, "completed_count": completed},
    )
