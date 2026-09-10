from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.matching.services import MatchingService

from .forms import TripForm
from .models import Trip


@login_required
def trip_create(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.driver = request.user
            trip.save()
            found = MatchingService().find_matches_for_trip(trip)
            if found:
                messages.success(
                    request,
                    f"Turen er oprettet. {len(found)} mulige matches fundet langs ruten.",
                )
            else:
                messages.success(request, "Turen er oprettet.")
            return redirect(trip)
    else:
        form = TripForm()
    return render(request, "trips/trip_form.html", {"form": form, "is_new": True})


@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    matches = trip.matches.select_related(
        "transport_request", "transport_request__owner"
    ).order_by("-match_score")
    return render(request, "trips/trip_detail.html", {"trip": trip, "matches": matches})


@login_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            MatchingService().find_matches_for_trip(trip)
            messages.success(request, "Turen er opdateret.")
            return redirect(trip)
    else:
        form = TripForm(instance=trip)
    return render(request, "trips/trip_form.html", {"form": form, "is_new": False})


@login_required
def trip_cancel(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    if request.method == "POST":
        trip.status = Trip.Status.CANCELLED
        trip.save(update_fields=["status"])
        messages.info(request, "Turen er annulleret.")
        return redirect("dashboard")
    return render(request, "trips/trip_confirm_cancel.html", {"trip": trip})
