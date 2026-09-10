from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from apps.bookings.models import Booking
from apps.notifications import services as notifications

from .forms import MessageForm


@login_required
def send_message(request, booking_pk):
    booking = get_object_or_404(Booking, pk=booking_pk)
    if request.user.id not in booking.participants():
        raise Http404
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.booking = booking
            message.sender = request.user
            message.save()
            notifications.notify_new_message(message)
    return redirect("booking_detail", pk=booking.pk)
