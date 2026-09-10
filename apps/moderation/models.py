from django.conf import settings
from django.db import models


class Report(models.Model):
    """Rapportering af mistænkelige opgaver eller adfærd, jf. PRD afsnit 19."""

    class Status(models.TextChoices):
        OPEN = "open", "Åben"
        RESOLVED = "resolved", "Behandlet"
        DISMISSED = "dismissed", "Afvist"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reports_made", verbose_name="Anmelder",
    )
    transport_request = models.ForeignKey(
        "transport.TransportRequest", on_delete=models.CASCADE,
        null=True, blank=True, related_name="reports",
    )
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.CASCADE,
        null=True, blank=True, related_name="reports",
    )
    reason = models.TextField("Begrundelse")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Rapport"
        verbose_name_plural = "Rapporter"

    def __str__(self):
        target = self.transport_request or self.booking
        return f"Rapport fra {self.reporter} om {target}"
