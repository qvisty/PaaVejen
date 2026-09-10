from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Bruger, jf. PRD afsnit 28."""

    phone = models.CharField("Telefon", max_length=20, blank=True)
    terms_accepted_at = models.DateTimeField(
        "Vilkår accepteret", null=True, blank=True,
        help_text="Hvornår brugeren accepterede vilkårene ved oprettelse.",
    )

    @property
    def average_rating(self) -> float | None:
        """Gennemsnitlig rating på tværs af gennemførte bookinger."""
        result = self.ratings_received.aggregate(avg=models.Avg("score"))
        return result["avg"]

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    def __str__(self):
        return self.display_name
