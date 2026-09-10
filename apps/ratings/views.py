from django.contrib import messages as flash
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.bookings.models import Booking
from apps.bookings.services import complete_if_rated

from .forms import RatingForm
from .models import Rating


@login_required
def rate_booking(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)
    if request.user.id not in booking.participants():
        raise Http404
    if booking.status not in (Booking.Status.DELIVERED, Booking.Status.COMPLETED):
        flash.error(request, "Bookingen kan først vurderes efter aflevering.")
        return redirect(booking)
    if Rating.objects.filter(booking=booking, reviewer=request.user).exists():
        flash.info(request, "Du har allerede givet en rating for denne booking.")
        return redirect(booking)

    reviewed_user = booking.customer if request.user.id == booking.driver_id else booking.driver

    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.booking = booking
            rating.reviewer = request.user
            rating.reviewed_user = reviewed_user
            rating.save()
            complete_if_rated(booking)
            flash.success(request, "Tak for din vurdering.")
            return redirect(booking)
    else:
        form = RatingForm()
    return render(
        request,
        "ratings/rating_form.html",
        {"form": form, "booking": booking, "reviewed_user": reviewed_user},
    )
