from django.conf import settings
from django.db import models


class PushConfig(models.Model):
    """VAPID nøglepar til web push, genereret én gang og gemt i databasen.

    Dermed kræver push ingen manuel nøgleopsætning i driftsmiljøet.
    """

    private_key_pem = models.TextField()
    public_key = models.CharField(
        max_length=255,
        help_text="Application server key i URL sikker base64, bruges af browseren.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Push konfiguration"
        verbose_name_plural = "Push konfiguration"

    def __str__(self):
        return f"VAPID nøglepar fra {self.created_at:%d.%m.%Y}"


class PushSubscription(models.Model):
    """En browsers push abonnement for en bruger, jf. PRD afsnit 22."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Push abonnement"
        verbose_name_plural = "Push abonnementer"

    def __str__(self):
        return f"Push til {self.user} ({self.endpoint[:40]}…)"
