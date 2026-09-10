from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.constants import SIZE_MOVING_BOX, SIZE_SMALL_BAG, SIZE_STATION_WAGON
from apps.core.geo import lookup_place
from apps.transport.models import TransportRequest
from apps.trips.models import Trip

from .models import Match
from .services import MatchingService

User = get_user_model()


def make_trip(driver, origin, destination, **overrides):
    origin_point = lookup_place(origin)
    destination_point = lookup_place(destination)
    defaults = {
        "driver": driver,
        "origin_name": origin,
        "origin_lat": origin_point.lat,
        "origin_lng": origin_point.lng,
        "destination_name": destination,
        "destination_lat": destination_point.lat,
        "destination_lng": destination_point.lng,
        "departure_time": timezone.now() + timedelta(days=1),
        "max_detour_minutes": 30,
        "capacity": SIZE_STATION_WAGON,
    }
    defaults.update(overrides)
    return Trip.objects.create(**defaults)


def make_request(owner, pickup, delivery, **overrides):
    pickup_point = lookup_place(pickup)
    delivery_point = lookup_place(delivery)
    defaults = {
        "owner": owner,
        "pickup_name": pickup,
        "pickup_lat": pickup_point.lat,
        "pickup_lng": pickup_point.lng,
        "delivery_name": delivery,
        "delivery_lat": delivery_point.lat,
        "delivery_lng": delivery_point.lng,
        "latest_delivery": timezone.now() + timedelta(days=3),
        "description": "En stol købt på DBA.",
        "size": SIZE_MOVING_BOX,
    }
    defaults.update(overrides)
    return TransportRequest.objects.create(**defaults)


class MatchingServiceTests(TestCase):
    """Scenariet fra PRD afsnit 57 og 60."""

    def setUp(self):
        self.driver = User.objects.create_user("martin", password="x")
        self.sender = User.objects.create_user("jesper", password="x")

    def test_kolding_soenderborg_trip_matches_kolding_aabenraa_request(self):
        trip = make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.trip, trip)
        self.assertGreater(match.match_score, 50)
        self.assertGreater(match.suggested_price, 0)
        self.assertLessEqual(match.detour_minutes, trip.max_detour_minutes)
        transport_request.refresh_from_db()
        self.assertEqual(transport_request.status, TransportRequest.Status.MATCHED)

    def test_trip_far_from_request_does_not_match(self):
        make_trip(self.driver, "Aarhus", "Aalborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(matches, [])

    def test_wrong_direction_does_not_match(self):
        # Turen kører nordpå, men varen skal sydpå.
        make_trip(self.driver, "Sønderborg", "Kolding")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(matches, [])

    def test_too_small_capacity_does_not_match(self):
        make_trip(self.driver, "Kolding", "Sønderborg", capacity=SIZE_SMALL_BAG)
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(matches, [])

    def test_departure_after_deadline_does_not_match(self):
        make_trip(
            self.driver, "Kolding", "Sønderborg",
            departure_time=timezone.now() + timedelta(days=5),
        )
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(matches, [])

    def test_own_trip_is_not_matched(self):
        make_trip(self.sender, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertEqual(matches, [])

    def test_find_matches_for_trip_finds_open_requests(self):
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        trip = make_trip(self.driver, "Kolding", "Sønderborg")

        matches = MatchingService().find_matches_for_trip(trip)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].transport_request, transport_request)

    def test_rerun_updates_existing_match_instead_of_duplicating(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")

        service = MatchingService()
        service.find_matches_for_request(transport_request)
        service.find_matches_for_request(transport_request)

        self.assertEqual(Match.objects.count(), 1)
