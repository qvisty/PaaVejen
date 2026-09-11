"""
Notifikationer, jf. PRD afsnit 22. Kanaler i MVP: e mail og web push.

Afsendelse må aldrig vælte selve handlingen, så alle kanaler fejler
stille, og brugere uden e mail eller push abonnement springes over.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

from .push import send_push

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return settings.PAAVEJEN.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _send(user, subject: str, body: str, path: str | None = None) -> None:
    url = f"{_base_url()}{path}" if path else _base_url()
    if user.email:
        try:
            send_mail(
                subject=f"PåVejen: {subject}",
                message=f"{body}\n\n{url}",
                from_email=None,  # DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            logger.warning("Kunne ikke sende mail til %s", user.email, exc_info=True)
    try:
        send_push(user, subject, body, url=url)
    except Exception:
        logger.exception("Kunne ikke sende push til %s", user)


def notify_new_match(match) -> None:
    """Nyt match: besked til både opgavens ejer og chaufføren."""
    transport_request = match.transport_request
    trip = match.trip
    _send(
        transport_request.owner,
        "Nyt match til din opgave",
        (
            f"{trip.driver.display_name} kører {trip.origin_name} → "
            f"{trip.destination_name} {trip.departure_time:%A d. %d/%m kl. %H:%M}. "
            f"Matchscore {match.match_score} %, cirka "
            f"{match.detour_minutes:.0f} minutters omvej, foreslået pris "
            f"{match.suggested_price} kr."
        ),
        path=transport_request.get_absolute_url(),
    )
    _send(
        trip.driver,
        "Ny mulighed på din tur",
        (
            f"En opgave passer til din tur {trip.origin_name} → "
            f"{trip.destination_name}: {transport_request.pickup_name} → "
            f"{transport_request.delivery_name} "
            f"({transport_request.get_size_display()}). "
            f"Cirka {match.detour_minutes:.0f} minutters ekstra kørsel, "
            f"{match.suggested_price} kr."
        ),
        path=trip.get_absolute_url(),
    )


def notify_booking_requested(booking) -> None:
    _send(
        booking.driver,
        "Ny forespørgsel",
        (
            f"{booking.customer.display_name} vil have noget med på din tur: "
            f"{booking.transport_request.pickup_name} → "
            f"{booking.transport_request.delivery_name} for "
            f"{booking.agreed_price} kr."
        ),
        path=booking.get_absolute_url(),
    )


def notify_booking_accepted(booking) -> None:
    _send(
        booking.customer,
        "Din forespørgsel er accepteret",
        (
            f"{booking.driver.display_name} har accepteret at tage "
            f"{booking.transport_request.pickup_name} → "
            f"{booking.transport_request.delivery_name} med. "
            "Din afhentningskode står på bookingsiden."
        ),
        path=booking.get_absolute_url(),
    )


def notify_booking_declined(booking) -> None:
    _send(
        booking.customer,
        "Forespørgslen blev afvist",
        (
            f"{booking.driver.display_name} kan desværre ikke tage opgaven "
            "denne gang. Se andre matches på din opgave."
        ),
        path=booking.transport_request.get_absolute_url(),
    )


def notify_pickup_confirmed(booking) -> None:
    _send(
        booking.customer,
        "Din vare er afhentet",
        (
            "Chaufføren har markeret varen som afhentet, og den er nu "
            "under transport."
        ),
        path=booking.get_absolute_url(),
    )


def notify_delivery_confirmed(booking) -> None:
    for user in (booking.customer, booking.driver):
        _send(
            user,
            "Varen er afleveret",
            "Leveringen er gennemført. Tak fordi du brugte PåVejen. "
            "Giv din vurdering på bookingsiden.",
            path=booking.get_absolute_url(),
        )


def notify_booking_cancelled(booking, by_user) -> None:
    other = booking.customer if by_user == booking.driver else booking.driver
    _send(
        other,
        "Booking annulleret",
        (
            f"{by_user.display_name} har annulleret bookingen "
            f"{booking.transport_request.pickup_name} → "
            f"{booking.transport_request.delivery_name}."
        ),
        path=booking.get_absolute_url(),
    )


def notify_dispute_opened(booking, by_user) -> None:
    other = booking.customer if by_user == booking.driver else booking.driver
    _send(
        other,
        "Der er markeret et problem",
        (
            f"{by_user.display_name} har markeret et problem på bookingen "
            f"{booking.transport_request.pickup_name} → "
            f"{booking.transport_request.delivery_name}. Betalingen er sat "
            "på pause, mens sagen behandles. Skriv din forklaring i chatten."
        ),
        path=booking.get_absolute_url(),
    )


def notify_dispute_resolved(booking, outcome_text: str) -> None:
    for user in (booking.customer, booking.driver):
        _send(
            user,
            "Konflikten er afgjort",
            outcome_text,
            path=booking.get_absolute_url(),
        )


def notify_new_message(message) -> None:
    booking = message.booking
    recipient = booking.customer if message.sender_id == booking.driver_id else booking.driver
    _send(
        recipient,
        f"Ny besked fra {message.sender.display_name}",
        message.content,
        path=booking.get_absolute_url(),
    )
