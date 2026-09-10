"""
Betalingslivscyklus, jf. PRD afsnit 14.

Reserveres ved accept. Frigives efter aflevering. Sættes på pause ved
konflikt. Providerabstraktionen er bevidst tynd: i piloten er provider
"manual", og en rigtig udbyder kobles på ved at erstatte disse
funktioner med kald til fx Stripe Connect.
"""
from django.conf import settings
from django.utils import timezone

from .models import Payment


def calculate_platform_fee(amount: int) -> int:
    percent = settings.PAAVEJEN.get("PLATFORM_FEE_PERCENT", 15)
    return round(amount * percent / 100)


def reserve_payment(booking) -> Payment:
    """Reservér betalingen, når chaufføren accepterer."""
    fee = calculate_platform_fee(booking.agreed_price)
    payment, _created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            "amount": booking.agreed_price,
            "platform_fee": fee,
            "driver_payout": booking.agreed_price - fee,
        },
    )
    return payment


def release_payment(booking) -> Payment | None:
    """Frigiv betalingen, efter aflevering eller efter en afgjort konflikt."""
    payment = getattr(booking, "payment", None)
    if payment is None or payment.status not in (
        Payment.Status.RESERVED, Payment.Status.ON_HOLD,
    ):
        return payment
    payment.status = Payment.Status.RELEASED
    payment.released_at = timezone.now()
    payment.save(update_fields=["status", "released_at"])
    return payment


def refund_payment(booking) -> Payment | None:
    """Refundér betalingen til afsenderen, fx efter en afgjort konflikt."""
    payment = getattr(booking, "payment", None)
    if payment is None or payment.status not in (
        Payment.Status.RESERVED, Payment.Status.ON_HOLD,
    ):
        return payment
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=["status"])
    return payment


def hold_payment(booking) -> Payment | None:
    """Sæt betalingen på pause ved konflikt."""
    payment = getattr(booking, "payment", None)
    if payment is None or payment.status != Payment.Status.RESERVED:
        return payment
    payment.status = Payment.Status.ON_HOLD
    payment.save(update_fields=["status"])
    return payment


def cancel_payment(booking) -> Payment | None:
    """Annullér reservationen, hvis bookingen annulleres før aflevering."""
    payment = getattr(booking, "payment", None)
    if payment is None or payment.status not in (
        Payment.Status.RESERVED, Payment.Status.ON_HOLD,
    ):
        return payment
    payment.status = Payment.Status.CANCELLED
    payment.save(update_fields=["status"])
    return payment
