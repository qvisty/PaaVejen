from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import SIZE_CHOICES, SIZE_TRUNK
from apps.core.geo import Point

WEEKDAY_CHOICES = [
    (0, "Mandag"),
    (1, "Tirsdag"),
    (2, "Onsdag"),
    (3, "Torsdag"),
    (4, "Fredag"),
    (5, "Lørdag"),
    (6, "Søndag"),
]


class RecurringTrip(models.Model):
    """En gentagen tur, fx pendling, jf. PRD afsnit 23.

    Gentagne ture materialiseres til konkrete Trip forekomster, når
    matchingmotoren har brug for dem, så resten af systemet kun kender
    almindelige ture.
    """

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="recurring_trips", verbose_name="Chauffør",
    )
    origin_name = models.CharField("Startsted", max_length=200)
    origin_lat = models.FloatField("Start breddegrad")
    origin_lng = models.FloatField("Start længdegrad")
    destination_name = models.CharField("Destination", max_length=200)
    destination_lat = models.FloatField("Destination breddegrad")
    destination_lng = models.FloatField("Destination længdegrad")
    weekdays = models.JSONField("Ugedage", default=list)
    departure_time = models.TimeField("Afgang cirka")
    max_detour_minutes = models.PositiveIntegerField(
        "Maksimal omvej i minutter", default=15,
    )
    capacity = models.CharField(
        "Ledig kapacitet", max_length=20, choices=SIZE_CHOICES, default=SIZE_TRUNK,
    )
    active = models.BooleanField("Aktiv", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gentagen tur"
        verbose_name_plural = "Gentagne ture"

    def weekday_labels(self) -> str:
        labels = dict(WEEKDAY_CHOICES)
        return ", ".join(labels[d] for d in sorted(self.weekdays) if d in labels)

    def upcoming_departures(self, start, end) -> list:
        """Konkrete afgangstidspunkter i [start, end], i lokal tid."""
        if not self.weekdays:
            return []
        tz = timezone.get_current_timezone()
        local_start = timezone.localtime(start, tz)
        departures = []
        day = local_start.date()
        while True:
            naive = datetime.combine(day, self.departure_time)
            candidate = timezone.make_aware(naive, tz)
            if candidate > end:
                break
            if candidate >= start and day.weekday() in self.weekdays:
                departures.append(candidate)
            day += timedelta(days=1)
        return departures

    def get_absolute_url(self):
        return reverse("recurring_detail", args=[self.pk])

    def __str__(self):
        return (
            f"{self.origin_name} → {self.destination_name} "
            f"({self.weekday_labels()} kl. {self.departure_time:%H:%M})"
        )


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
    recurring_trip = models.ForeignKey(
        RecurringTrip, on_delete=models.CASCADE, null=True, blank=True,
        related_name="trips", verbose_name="Gentagen tur",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["departure_time"]
        verbose_name = "Tur"
        verbose_name_plural = "Ture"
        constraints = [
            models.UniqueConstraint(
                fields=["recurring_trip", "departure_time"],
                condition=models.Q(recurring_trip__isnull=False),
                name="unique_recurring_occurrence",
            ),
        ]

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
