from django.db import models

from apps.bookings.models import Booking


class Payment(models.Model):
    """Betaling for en booking, jf. PRD afsnit 13, 14 og 28.

    I den lukkede pilot afregnes der uden om platformen, men reservér og
    frigiv livscyklussen føres her, så flow, gebyr og konflikthåndtering
    er på plads. provider er "manual", indtil en rigtig udbyder som
    Stripe Connect kobles på i fase 3.
    """

    class Status(models.TextChoices):
        RESERVED = "reserved", "Reserveret"
        RELEASED = "released", "Frigivet"
        ON_HOLD = "on_hold", "På pause"
        REFUNDED = "refunded", "Refunderet"
        CANCELLED = "cancelled", "Annulleret"

    booking = models.OneToOneField(
        Booking, on_delete=models.PROTECT, related_name="payment",
    )
    provider = models.CharField("Udbyder", max_length=30, default="manual")
    provider_reference = models.CharField(
        "Udbyderreference", max_length=100, blank=True,
    )
    amount = models.PositiveIntegerField("Beløb i kr.")
    platform_fee = models.PositiveIntegerField("Platformsgebyr i kr.")
    driver_payout = models.PositiveIntegerField("Til chaufføren i kr.")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RESERVED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Betaling"
        verbose_name_plural = "Betalinger"

    def __str__(self):
        return f"Betaling {self.amount} kr. for booking #{self.booking_id} ({self.get_status_display()})"
