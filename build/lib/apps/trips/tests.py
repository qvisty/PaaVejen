from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.constants import SIZE_STATION_WAGON
from apps.core.geo import lookup_place
from apps.matching.services import MatchingService
from apps.matching.tests import make_request

from .models import RecurringTrip, Trip
from .services import materialize_recurring_trips

User = get_user_model()


def make_recurring(driver, origin, destination, **overrides):
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
        "weekdays": [0, 1, 2, 3, 4],  # hverdage
        "departure_time": time(7, 0),
        "max_detour_minutes": 20,
        "capacity": SIZE_STATION_WAGON,
    }
    defaults.update(overrides)
    return RecurringTrip.objects.create(**defaults)


class RecurringTripTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user("pendler", password="x")
        self.sender = User.objects.create_user("jesper", password="x")

    def test_upcoming_departures_respects_weekdays_and_window(self):
        recurring = make_recurring(self.driver, "Aabenraa", "Tønder")
        start = timezone.now()
        end = start + timedelta(days=7)
        departures = recurring.upcoming_departures(start, end)

        # Fem hverdage på en uge.
        self.assertEqual(len(departures), 5)
        for departure in departures:
            local = timezone.localtime(departure)
            self.assertIn(local.weekday(), [0, 1, 2, 3, 4])
            self.assertEqual((local.hour, local.minute), (7, 0))
            self.assertGreaterEqual(departure, start)
            self.assertLessEqual(departure, end)

    def test_materialize_creates_trips_once(self):
        recurring = make_recurring(self.driver, "Aabenraa", "Tønder")
        start = timezone.now()
        end = start + timedelta(days=7)

        first = materialize_recurring_trips(start, end)
        second = materialize_recurring_trips(start, end)

        self.assertEqual(len(first), 5)
        self.assertEqual(second, [])
        self.assertEqual(recurring.trips.count(), 5)
        trip = recurring.trips.first()
        self.assertEqual(trip.driver, self.driver)
        self.assertEqual(trip.capacity, recurring.capacity)

    def test_inactive_recurring_is_not_materialized(self):
        make_recurring(self.driver, "Aabenraa", "Tønder", active=False)
        start = timezone.now()
        created = materialize_recurring_trips(start, start + timedelta(days=7))
        self.assertEqual(created, [])

    def test_request_matches_recurring_trip(self):
        """PRD afsnit 23: nye opgaver matches automatisk mod gentagne ture."""
        make_recurring(self.driver, "Aabenraa", "Tønder")
        transport_request = make_request(
            self.sender, "Aabenraa", "Tønder",
            latest_delivery=timezone.now() + timedelta(days=4),
        )

        matches = MatchingService().find_matches_for_request(transport_request)

        self.assertGreater(len(matches), 0)
        self.assertTrue(
            all(m.trip.recurring_trip is not None for m in matches)
        )

    def test_own_recurring_trip_is_not_matched(self):
        make_recurring(self.sender, "Aabenraa", "Tønder")
        transport_request = make_request(
            self.sender, "Aabenraa", "Tønder",
            latest_delivery=timezone.now() + timedelta(days=4),
        )
        matches = MatchingService().find_matches_for_request(transport_request)
        self.assertEqual(matches, [])
        self.assertEqual(Trip.objects.count(), 0)
