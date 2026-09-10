from django.conf import settings
from django.db import models

from apps.bookings.models import Booking


class Message(models.Model):
    """Chatbesked på en booking, jf. PRD afsnit 21.

    sender er None for systembeskeder, fx statusændringer.
    """

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="messages_sent",
    )
    content = models.TextField("Besked")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Besked"
        verbose_name_plural = "Beskeder"

    @property
    def is_system(self) -> bool:
        return self.sender_id is None

    def __str__(self):
        who = self.sender or "System"
        return f"{who}: {self.content[:50]}"
