"""Slet tidsstemplede testbrugere fra verifikationskørsler.

Rammer kun brugernavne på den præcise form demo-<navn>-<seks cifre>,
som verifikationsscriptet opretter, aldrig rigtige brugere. Tilhørende
bookinger og betalinger fjernes først, da de er beskyttet mod kaskade.
"""
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

User = get_user_model()

DEMO_PATTERN = re.compile(r"^demo-[a-z]+-\d{6}$")


class Command(BaseCommand):
    help = "Sletter testbrugere med navne på formen demo-<navn>-<seks cifre>."

    @transaction.atomic
    def handle(self, *args, **options):
        demo_users = [
            user for user in User.objects.filter(username__startswith="demo-")
            if DEMO_PATTERN.match(user.username)
        ]
        if not demo_users:
            self.stdout.write("Ingen testbrugere at slette.")
            return
        from apps.bookings.models import Booking
        from apps.payments.models import Payment

        bookings = Booking.objects.filter(
            Q(driver__in=demo_users) | Q(customer__in=demo_users)
        )
        Payment.objects.filter(booking__in=bookings).delete()
        bookings.delete()
        for user in demo_users:
            self.stdout.write(f"Sletter {user.username}")
            user.delete()
        self.stdout.write(self.style.SUCCESS(f"{len(demo_users)} testbrugere slettet."))
