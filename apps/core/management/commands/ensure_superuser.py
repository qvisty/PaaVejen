"""Opret en superbruger ud fra miljøvariabler, hvis den ikke findes.

Bruges ved deploy: DJANGO_SUPERUSER_USERNAME og DJANGO_SUPERUSER_PASSWORD
sættes i driftsmiljøet, aldrig i repoet. Kommandoen er idempotent og
rører ikke en eksisterende bruger, så et ændret kodeord bevares.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Opretter superbrugeren fra DJANGO_SUPERUSER_* miljøvariabler, hvis den mangler."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not username or not password:
            self.stdout.write("Springer over: DJANGO_SUPERUSER_* er ikke sat.")
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superbrugeren {username} findes allerede.")
            return
        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f"Superbrugeren {username} er oprettet."))
