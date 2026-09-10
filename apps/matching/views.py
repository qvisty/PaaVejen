from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.bookings.services import create_booking_request

from .models import Match


@login_required
def send_request(request, pk):
    """Afsenderen sender en forespørgsel til chaufføren, jf. PRD Flow C."""
    match = get_object_or_404(
        Match, pk=pk, transport_request__owner=request.user,
        status=Match.Status.SUGGESTED,
    )
    if request.method == "POST":
        booking = create_booking_request(match)
        messages.success(
            request,
            f"Forespørgslen er sendt til {booking.driver.display_name}. "
            "Du får besked, når der svares.",
        )
        return redirect("booking_detail", pk=booking.pk)
    return redirect("request_detail", pk=match.transport_request.pk)
