from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.constants import SIZE_CHOICES, SIZE_TRUNK
from apps.core.geo import Point


class Trip(models.Model):
    """En planlagt tur, jf. PRD afsnit 28 og 29."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Aktiv"
        MATCHED = "matched", "Matchet"
        COMPLETED = "completed", "Gennemført"
        CANCELLED = "cancelled", "Annulleret"

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips",
        verbose_name="Chauffør",
    )
    origin_name = models.CharField("Startsted", max_length=200)
    origin_lat = models.FloatField("Start breddegrad")
    origin_lng = models.FloatField("Start længdegrad")
    destination_name = models.CharField("Destination", max_length=200)
    destination_lat = models.FloatField("Destination breddegrad")
    destination_lng = models.FloatField("Destination længdegrad")
    departure_time = models.DateTimeField("Afgang cirka")
    max_detour_minutes = models.PositiveIntegerField(
        "Maksimal omvej i minutter", default=15,
    )
    capacity = models.CharField(
        "Ledig kapacitet", max_length=20, choices=SIZE_CHOICES, default=SIZE_TRUNK,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["departure_time"]
        verbose_name = "Tur"
        verbose_name_plural = "Ture"

    @property
    def origin_point(self) -> Point:
        return Point(self.origin_lat, self.origin_lng)

    @property
    def destination_point(self) -> Point:
        return Point(self.destination_lat, self.destination_lng)

    def get_absolute_url(self):
        return reverse("trip_detail", args=[self.pk])

    def __str__(self):
        return f"{self.origin_name} → {self.destination_name} ({self.departure_time:%d.%m %H:%M})"
