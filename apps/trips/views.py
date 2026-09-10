from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.matching.services import MatchingService

from .forms import RecurringTripForm, TripForm
from .models import RecurringTrip, Trip
from .services import materialize_recurring_trips

# Hvor langt frem gentagne ture materialiseres, når de oprettes.
MATERIALIZE_DAYS_AHEAD = 14


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
def recurring_create(request):
    if request.method == "POST":
        form = RecurringTripForm(request.POST)
        if form.is_valid():
            recurring = form.save(commit=False)
            recurring.driver = request.user
            recurring.save()
            matches = _materialize_and_match(recurring)
            if matches:
                messages.success(
                    request,
                    f"Den gentagne tur er oprettet. {matches} mulige matches "
                    "fundet langs ruten.",
                )
            else:
                messages.success(request, "Den gentagne tur er oprettet.")
            return redirect(recurring)
    else:
        form = RecurringTripForm()
    return render(
        request, "trips/recurring_form.html", {"form": form, "is_new": True},
    )


@login_required
def recurring_detail(request, pk):
    recurring = get_object_or_404(RecurringTrip, pk=pk, driver=request.user)
    trips = recurring.trips.filter(
        departure_time__gte=timezone.now()
    ).prefetch_related("matches__transport_request")
    return render(
        request,
        "trips/recurring_detail.html",
        {"recurring": recurring, "trips": trips},
    )


@login_required
def recurring_edit(request, pk):
    recurring = get_object_or_404(RecurringTrip, pk=pk, driver=request.user)
    if request.method == "POST":
        form = RecurringTripForm(request.POST, instance=recurring)
        if form.is_valid():
            form.save()
            # Fjern fremtidige forekomster uden booking og materialisér forfra.
            recurring.trips.filter(
                departure_time__gte=timezone.now(), status=Trip.Status.ACTIVE,
            ).delete()
            _materialize_and_match(recurring)
            messages.success(request, "Den gentagne tur er opdateret.")
            return redirect(recurring)
    else:
        form = RecurringTripForm(instance=recurring)
    return render(
        request, "trips/recurring_form.html", {"form": form, "is_new": False},
    )


@login_required
def recurring_deactivate(request, pk):
    recurring = get_object_or_404(RecurringTrip, pk=pk, driver=request.user)
    if request.method == "POST":
        recurring.active = False
        recurring.save(update_fields=["active"])
        recurring.trips.filter(
            departure_time__gte=timezone.now(), status=Trip.Status.ACTIVE,
        ).delete()
        messages.info(request, "Den gentagne tur er deaktiveret.")
        return redirect("dashboard")
    return render(
        request, "trips/recurring_confirm_deactivate.html", {"recurring": recurring},
    )


def _materialize_and_match(recurring: RecurringTrip) -> int:
    now = timezone.now()
    created = materialize_recurring_trips(
        start=now, end=now + timedelta(days=MATERIALIZE_DAYS_AHEAD),
    )
    service = MatchingService()
    total = 0
    for trip in created:
        if trip.recurring_trip_id == recurring.pk:
            total += len(service.find_matches_for_trip(trip))
    return total


@login_required
def trip_cancel(request, pk):
    trip = get_object_or_404(Trip, pk=pk, driver=request.user)
    if request.method == "POST":
        trip.status = Trip.Status.CANCELLED
        trip.save(update_fields=["status"])
        messages.info(request, "Turen er annulleret.")
        return redirect("dashboard")
    return render(request, "trips/trip_confirm_cancel.html", {"trip": trip})
