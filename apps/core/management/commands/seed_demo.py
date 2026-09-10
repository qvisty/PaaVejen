"""Opret demodata til udvikling og fremvisning.

Brug: python manage.py seed_demo
Kør kun på en tom eller lokal database.
"""
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings import services as booking_services
from apps.core.constants import SIZE_MOVING_BOX, SIZE_STATION_WAGON
from apps.core.geo import lookup_place
from apps.matching.services import MatchingService
from apps.messaging.models import Message
from apps.transport.models import TransportRequest
from apps.trips.models import RecurringTrip, Trip

User = get_user_model()

PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Opretter demobrugere, ture, opgaver, matches og en aktiv booking."

    def handle(self, *args, **options):
        jesper, _ = User.objects.get_or_create(
            username="jesper",
            defaults={"email": "jesper@example.com", "first_name": "Jesper"},
        )
        jesper.set_password(PASSWORD)
        jesper.save()
        martin, _ = User.objects.get_or_create(
            username="martin",
            defaults={"email": "martin@example.com", "first_name": "Martin"},
        )
        martin.set_password(PASSWORD)
        martin.save()

        def place(name):
            return lookup_place(name)

        kolding, soenderborg = place("Kolding"), place("Sønderborg")
        aabenraa = place("Aabenraa")

        trip = Trip.objects.create(
            driver=martin,
            origin_name="Kolding", origin_lat=kolding.lat, origin_lng=kolding.lng,
            destination_name="Sønderborg",
            destination_lat=soenderborg.lat, destination_lng=soenderborg.lng,
            departure_time=timezone.now() + timedelta(days=2),
            max_detour_minutes=20, capacity=SIZE_STATION_WAGON,
        )
        RecurringTrip.objects.get_or_create(
            driver=martin,
            origin_name="Aabenraa", origin_lat=aabenraa.lat, origin_lng=aabenraa.lng,
            destination_name="Tønder",
            destination_lat=place("Tønder").lat, destination_lng=place("Tønder").lng,
            defaults={
                "weekdays": [0, 1, 2, 3, 4],
                "departure_time": time(7, 0),
                "max_detour_minutes": 20,
                "capacity": SIZE_STATION_WAGON,
            },
        )

        request = TransportRequest.objects.create(
            owner=jesper,
            pickup_name="Kolding", pickup_lat=kolding.lat, pickup_lng=kolding.lng,
            delivery_name="Aabenraa",
            delivery_lat=aabenraa.lat, delivery_lng=aabenraa.lng,
            latest_delivery=timezone.now() + timedelta(days=4),
            description="En stol købt på DBA. Let, men lidt kluntet.",
            size=SIZE_MOVING_BOX, estimated_value=400,
        )
        matches = MatchingService().find_matches_for_request(request)

        if matches:
            booking = booking_services.create_booking_request(matches[0])
            booking_services.accept_booking(booking)
            Message.objects.create(
                booking=booking, sender=jesper,
                content="Stolen står klar ved døren fra kl. 14.",
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demodata klar. Log ind som jesper eller martin med kodeordet {PASSWORD}. "
            f"Tur #{trip.pk}, opgave #{request.pk}, {len(matches)} matches."
        ))
