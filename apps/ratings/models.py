from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.bookings.models import Booking


class Rating(models.Model):
    """Gensidig rating efter gennemført opgave, jf. PRD afsnit 16."""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="ratings")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_given",
    )
    reviewed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings_received",
    )
    score = models.PositiveIntegerField(
        "Stjerner", validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField("Kommentar", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "reviewer"], name="unique_rating_per_reviewer",
            ),
        ]
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"{self.reviewer} → {self.reviewed_user}: {self.score} stjerner"
