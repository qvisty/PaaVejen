from django.contrib import messages as flash
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.messaging.forms import MessageForm
from apps.ratings.models import Rating

from . import services
from .models import Booking


def _get_booking_for(user, pk) -> Booking:
    booking = get_object_or_404(
        Booking.objects.select_related(
            "match", "match__trip", "match__transport_request", "driver", "customer",
        ),
        pk=pk,
    )
    if user.id not in booking.participants():
        raise Http404
    return booking


@login_required
def booking_detail(request, pk):
    booking = _get_booking_for(request.user, pk)
    is_driver = request.user.id == booking.driver_id
    chat_messages = booking.messages.select_related("sender")
    my_rating = Rating.objects.filter(booking=booking, reviewer=request.user).first()
    return render(
        request,
        "bookings/booking_detail.html",
        {
            "booking": booking,
            "is_driver": is_driver,
            "chat_messages": chat_messages,
            "message_form": MessageForm(),
            "my_rating": my_rating,
        },
    )


@login_required
def booking_accept(request, pk):
    booking = _get_booking_for(request.user, pk)
    if request.method == "POST" and request.user.id == booking.driver_id:
        try:
            services.accept_booking(booking)
            flash.success(request, "Du har accepteret opgaven. God tur.")
        except services.BookingError as error:
            flash.error(request, str(error))
    return redirect(booking)


@login_required
def booking_decline(request, pk):
    booking = _get_booking_for(request.user, pk)
    if request.method == "POST" and request.user.id == booking.driver_id:
        try:
            services.decline_booking(booking)
            flash.info(request, "Du har afvist forespørgslen.")
        except services.BookingError as error:
            flash.error(request, str(error))
    return redirect(booking)


@login_required
def booking_pickup(request, pk):
    booking = _get_booking_for(request.user, pk)
    if request.method == "POST" and request.user.id == booking.driver_id:
        code = request.POST.get("code", "")
        try:
            services.confirm_pickup(booking, code)
            flash.success(request, "Afhentning registreret. Varen er under transport.")
        except services.BookingError as error:
            flash.error(request, str(error))
    return redirect(booking)


@login_required
def booking_deliver(request, pk):
    booking = _get_booking_for(request.user, pk)
    if request.method == "POST" and request.user.id == booking.driver_id:
        code = request.POST.get("code", "")
        try:
            services.confirm_delivery(booking, code)
            flash.success(request, "Aflevering registreret. Tak for turen.")
        except services.BookingError as error:
            flash.error(request, str(error))
    return redirect(booking)
