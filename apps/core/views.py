from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from apps.bookings.models import Booking
from apps.matching.models import Match
from apps.transport.models import TransportRequest
from apps.trips.models import RecurringTrip, Trip


def home(request):
    """Forsiden: to store valg, jf. PRD afsnit 39."""
    if request.user.is_authenticated:
        return dashboard(request)
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    user = request.user
    trips = (
        Trip.objects.filter(driver=user, recurring_trip__isnull=True)
        .exclude(status=Trip.Status.CANCELLED)
    )
    recurring_trips = RecurringTrip.objects.filter(driver=user, active=True)
    transport_requests = TransportRequest.objects.filter(owner=user).exclude(
        status=TransportRequest.Status.CANCELLED
    )
    new_matches = Match.objects.filter(
        transport_request__owner=user, status=Match.Status.SUGGESTED
    ).select_related("trip", "transport_request", "trip__driver")
    incoming_bookings = Booking.objects.filter(
        driver=user, status=Booking.Status.PENDING
    ).select_related("match", "customer", "match__transport_request")
    active_bookings = (
        Booking.objects.filter(status__in=Booking.ACTIVE_STATUSES)
        .filter(Q(driver=user) | Q(customer=user))
        .select_related("match", "driver", "customer", "match__transport_request")
    )
    return render(
        request,
        "core/dashboard.html",
        {
            "trips": trips,
            "recurring_trips": recurring_trips,
            "transport_requests": transport_requests,
            "new_matches": new_matches,
            "incoming_bookings": incoming_bookings,
            "active_bookings": active_bookings,
        },
    )
