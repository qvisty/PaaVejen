import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.matching.models import Match


def generate_code() -> str:
    """Firecifret kode til afhentning og aflevering, jf. PRD afsnit 17."""
    return f"{secrets.randbelow(10000):04d}"


class Booking(models.Model):
    """En aftalt transport, jf. PRD afsnit 28 og 29."""

    class Status(models.TextChoices):
        PENDING = "pending", "Afventer svar"
        ACCEPTED = "accepted", "Accepteret"
        COLLECTED = "collected", "Afhentet"
        DELIVERED = "delivered", "Afleveret"
        COMPLETED = "completed", "Afsluttet"
        CANCELLED = "cancelled", "Annulleret"
        DISPUTED = "disputed", "I konflikt"

    ACTIVE_STATUSES = [Status.PENDING, Status.ACCEPTED, Status.COLLECTED, Status.DELIVERED]

    match = models.OneToOneField(Match, on_delete=models.PROTECT, related_name="booking")
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="bookings_as_driver", verbose_name="Chauffør",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="bookings_as_customer", verbose_name="Afsender",
    )
    agreed_price = models.PositiveIntegerField("Aftalt pris i kr.")
    pickup_code = models.CharField(max_length=4, blank=True)
    delivery_code = models.CharField(max_length=4, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking"
        verbose_name_plural = "Bookinger"

    @property
    def transport_request(self):
        return self.match.transport_request

    @property
    def trip(self):
        return self.match.trip

    def participants(self):
        return {self.driver_id, self.customer_id}

    def get_absolute_url(self):
        return reverse("booking_detail", args=[self.pk])

    def __str__(self):
        return f"Booking #{self.pk}: {self.match.transport_request}"
