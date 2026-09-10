from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.core.constants import SIZE_CHOICES, SIZE_MOVING_BOX
from apps.core.geo import Point


def validate_image_size(image):
    max_mb = 5
    if image and image.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Billedet må højst fylde {max_mb} MB.")


def validate_max_value(value):
    """Prototypen har en maksimal accepteret vareværdi, jf. PRD afsnit 18."""
    max_value = settings.PAAVEJEN["MAX_ITEM_VALUE"]
    if value is not None and value > max_value:
        raise ValidationError(
            f"Varer over {max_value} kr. kan ikke transporteres via PåVejen endnu."
        )


class TransportRequest(models.Model):
    """Et transportbehov, jf. PRD afsnit 28 og 29."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Kladde"
        PUBLISHED = "published", "Offentliggjort"
        MATCHED = "matched", "Matchet"
        BOOKED = "booked", "Booket"
        COLLECTED = "collected", "Afhentet"
        IN_TRANSIT = "in_transit", "Under transport"
        DELIVERED = "delivered", "Afleveret"
        COMPLETED = "completed", "Afsluttet"
        CANCELLED = "cancelled", "Annulleret"
        DISPUTED = "disputed", "I konflikt"

    class Category(models.TextChoices):
        BRING_ALONG = "bring_along", "Tag med"
        PICK_UP = "pick_up", "Hent for mig"
        DROP_OFF = "drop_off", "Aflever for mig"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="transport_requests", verbose_name="Ejer",
    )
    category = models.CharField(
        "Opgavetype", max_length=20, choices=Category.choices,
        default=Category.BRING_ALONG,
    )
    pickup_name = models.CharField("Afhentningssted", max_length=200)
    pickup_lat = models.FloatField("Afhentning breddegrad")
    pickup_lng = models.FloatField("Afhentning længdegrad")
    delivery_name = models.CharField("Afleveringssted", max_length=200)
    delivery_lat = models.FloatField("Aflevering breddegrad")
    delivery_lng = models.FloatField("Aflevering længdegrad")
    earliest_pickup = models.DateTimeField("Tidligste afhentning", null=True, blank=True)
    latest_delivery = models.DateTimeField("Seneste aflevering")
    description = models.TextField("Beskrivelse")
    size = models.CharField(
        "Størrelse", max_length=20, choices=SIZE_CHOICES, default=SIZE_MOVING_BOX,
    )
    weight_kg = models.PositiveIntegerField("Vægt cirka kg", null=True, blank=True)
    estimated_value = models.PositiveIntegerField(
        "Cirka værdi i kr.", null=True, blank=True, validators=[validate_max_value],
    )
    image = models.ImageField(
        "Billede", upload_to="opgaver/", null=True, blank=True,
        validators=[validate_image_size],
    )
    terms_accepted = models.BooleanField(
        "Vilkår bekræftet", default=False,
        help_text="Ejeren har bekræftet, at varen ikke er en forbudt genstand.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PUBLISHED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transportopgave"
        verbose_name_plural = "Transportopgaver"

    @property
    def pickup_point(self) -> Point:
        return Point(self.pickup_lat, self.pickup_lng)

    @property
    def delivery_point(self) -> Point:
        return Point(self.delivery_lat, self.delivery_lng)

    def get_absolute_url(self):
        return reverse("request_detail", args=[self.pk])

    def __str__(self):
        return f"{self.pickup_name} → {self.delivery_name} ({self.get_size_display()})"
