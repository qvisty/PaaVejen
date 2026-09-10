from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Auditspor for væsentlige handlinger, jf. PRD afsnit 17 og 28."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_events",
    )
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_events",
    )
    event_type = models.CharField("Hændelse", max_length=50)
    metadata = models.JSONField("Metadata", default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audithændelse"
        verbose_name_plural = "Audithændelser"

    def __str__(self):
        return f"{self.timestamp:%d.%m %H:%M} {self.event_type}"
