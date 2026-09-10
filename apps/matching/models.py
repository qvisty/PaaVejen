from django.db import models

from apps.transport.models import TransportRequest
from apps.trips.models import Trip


class Match(models.Model):
    """Et foreslået match mellem en tur og en transportopgave, jf. PRD afsnit 28."""

    class Status(models.TextChoices):
        SUGGESTED = "suggested", "Foreslået"
        REQUESTED = "requested", "Forespurgt"
        ACCEPTED = "accepted", "Accepteret"
        DECLINED = "declined", "Afvist"
        EXPIRED = "expired", "Udløbet"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="matches")
    transport_request = models.ForeignKey(
        TransportRequest, on_delete=models.CASCADE, related_name="matches",
    )
    match_score = models.PositiveIntegerField("Matchscore i procent")
    detour_km = models.FloatField("Omvej i km")
    detour_minutes = models.FloatField("Omvej i minutter")
    suggested_price = models.PositiveIntegerField("Foreslået pris i kr.")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUGGESTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-match_score"]
        constraints = [
            models.UniqueConstraint(
                fields=["trip", "transport_request"], name="unique_trip_request_match",
            ),
        ]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return (
            f"{self.match_score} % match: {self.transport_request} "
            f"på {self.trip}"
        )
