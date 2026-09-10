"""
Bookingflowet, jf. PRD Flow C, D og E.

Statusovergange holdes samlet her, så views forbliver tynde, og så
auditspor og systembeskeder altid følger med en overgang.
"""
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log
from apps.matching.models import Match
from apps.messaging.models import Message
from apps.notifications import services as notifications
from apps.transport.models import TransportRequest
from apps.trips.models import Trip

from .models import Booking, generate_code


class BookingError(Exception):
    pass


@transaction.atomic
def create_booking_request(match: Match) -> Booking:
    """Afsenderen sender en forespørgsel til chaufføren."""
    if match.status != Match.Status.SUGGESTED:
        raise BookingError("Dette match kan ikke længere forespørges.")
    booking = Booking.objects.create(
        match=match,
        driver=match.trip.driver,
        customer=match.transport_request.owner,
        agreed_price=match.suggested_price,
    )
    match.status = Match.Status.REQUESTED
    match.save(update_fields=["status"])
    Message.objects.create(
        booking=booking,
        sender=None,
        content=(
            f"{booking.customer.display_name} har sendt en forespørgsel: "
            f"{match.transport_request.pickup_name} → "
            f"{match.transport_request.delivery_name} for {booking.agreed_price} kr."
        ),
    )
    notifications.notify_booking_requested(booking)
    log("booking_requested", user=booking.customer, booking=booking,
        price=booking.agreed_price)
    return booking


@transaction.atomic
def accept_booking(booking: Booking) -> Booking:
    """Chaufføren accepterer. Koder genereres, og opgaven bookes."""
    if booking.status != Booking.Status.PENDING:
        raise BookingError("Bookingen afventer ikke svar.")
    booking.status = Booking.Status.ACCEPTED
    booking.accepted_at = timezone.now()
    booking.pickup_code = generate_code()
    booking.delivery_code = generate_code()
    booking.save()

    match = booking.match
    match.status = Match.Status.ACCEPTED
    match.save(update_fields=["status"])

    transport_request = match.transport_request
    transport_request.status = TransportRequest.Status.BOOKED
    transport_request.save(update_fields=["status"])

    trip = match.trip
    trip.status = Trip.Status.MATCHED
    trip.save(update_fields=["status"])

    Message.objects.create(
        booking=booking, sender=None,
        content=f"{booking.driver.display_name} har accepteret forespørgslen.",
    )
    notifications.notify_booking_accepted(booking)
    log("booking_accepted", user=booking.driver, booking=booking)
    return booking


@transaction.atomic
def decline_booking(booking: Booking) -> Booking:
    if booking.status != Booking.Status.PENDING:
        raise BookingError("Bookingen afventer ikke svar.")
    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])
    match = booking.match
    match.status = Match.Status.DECLINED
    match.save(update_fields=["status"])
    Message.objects.create(
        booking=booking, sender=None,
        content=f"{booking.driver.display_name} har afvist forespørgslen.",
    )
    notifications.notify_booking_declined(booking)
    log("booking_declined", user=booking.driver, booking=booking)
    return booking


@transaction.atomic
def confirm_pickup(booking: Booking, code: str) -> Booking:
    """Chaufføren bekræfter afhentning med koden fra afsenderen."""
    if booking.status != Booking.Status.ACCEPTED:
        raise BookingError("Bookingen er ikke klar til afhentning.")
    if code.strip() != booking.pickup_code:
        raise BookingError("Forkert afhentningskode.")
    booking.status = Booking.Status.COLLECTED
    booking.collected_at = timezone.now()
    booking.save(update_fields=["status", "collected_at"])

    transport_request = booking.transport_request
    transport_request.status = TransportRequest.Status.IN_TRANSIT
    transport_request.save(update_fields=["status"])

    Message.objects.create(
        booking=booking, sender=None,
        content="Chaufføren har markeret varen som afhentet. Varen er under transport.",
    )
    notifications.notify_pickup_confirmed(booking)
    log("pickup_confirmed", user=booking.driver, booking=booking)
    return booking


@transaction.atomic
def confirm_delivery(booking: Booking, code: str) -> Booking:
    """Chaufføren bekræfter aflevering med koden fra modtageren."""
    if booking.status != Booking.Status.COLLECTED:
        raise BookingError("Varen er ikke under transport.")
    if code.strip() != booking.delivery_code:
        raise BookingError("Forkert afleveringskode.")
    booking.status = Booking.Status.DELIVERED
    booking.delivered_at = timezone.now()
    booking.save(update_fields=["status", "delivered_at"])

    transport_request = booking.transport_request
    transport_request.status = TransportRequest.Status.DELIVERED
    transport_request.save(update_fields=["status"])

    trip = booking.trip
    trip.status = Trip.Status.COMPLETED
    trip.save(update_fields=["status"])

    Message.objects.create(
        booking=booking, sender=None,
        content="Varen er afleveret. Begge parter kan nu give en rating.",
    )
    notifications.notify_delivery_confirmed(booking)
    log("delivery_confirmed", user=booking.driver, booking=booking)
    return booking


@transaction.atomic
def complete_if_rated(booking: Booking) -> Booking:
    """Afslut bookingen, når begge parter har givet rating."""
    if booking.status != Booking.Status.DELIVERED:
        return booking
    if booking.ratings.count() >= 2:
        booking.status = Booking.Status.COMPLETED
        booking.save(update_fields=["status"])
        transport_request = booking.transport_request
        transport_request.status = TransportRequest.Status.COMPLETED
        transport_request.save(update_fields=["status"])
        log("booking_completed", booking=booking)
    return booking
