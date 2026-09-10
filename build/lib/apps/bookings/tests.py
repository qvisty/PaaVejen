from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.matching.models import Match
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip
from apps.ratings.models import Rating
from apps.transport.models import TransportRequest
from apps.trips.models import Trip

from . import services
from .models import Booking

User = get_user_model()


class BookingFlowTests(TestCase):
    """Ende til ende flowet fra PRD afsnit 60."""

    def setUp(self):
        self.driver = User.objects.create_user("martin", password="x")
        self.sender = User.objects.create_user("jesper", password="x")
        self.trip = make_trip(self.driver, "Kolding", "Sønderborg")
        self.transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        self.match = MatchingService().find_matches_for_request(self.transport_request)[0]

    def test_full_flow(self):
        # 1. Afsenderen sender forespørgsel.
        booking = services.create_booking_request(self.match)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.driver, self.driver)
        self.assertEqual(booking.customer, self.sender)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.REQUESTED)

        # 2. Chaufføren accepterer, og koder genereres.
        services.accept_booking(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACCEPTED)
        self.assertEqual(len(booking.pickup_code), 4)
        self.assertEqual(len(booking.delivery_code), 4)
        self.transport_request.refresh_from_db()
        self.assertEqual(self.transport_request.status, TransportRequest.Status.BOOKED)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, Trip.Status.MATCHED)

        # 3. Forkert afhentningskode afvises.
        with self.assertRaises(services.BookingError):
            services.confirm_pickup(booking, "0000" if booking.pickup_code != "0000" else "1111")

        # 4. Afhentning med korrekt kode.
        services.confirm_pickup(booking, booking.pickup_code)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COLLECTED)
        self.transport_request.refresh_from_db()
        self.assertEqual(self.transport_request.status, TransportRequest.Status.IN_TRANSIT)

        # 5. Aflevering med korrekt kode.
        services.confirm_delivery(booking, booking.delivery_code)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.DELIVERED)
        self.transport_request.refresh_from_db()
        self.assertEqual(self.transport_request.status, TransportRequest.Status.DELIVERED)

        # 6. Begge parter giver rating, og bookingen afsluttes.
        Rating.objects.create(
            booking=booking, reviewer=self.sender, reviewed_user=self.driver, score=5,
        )
        services.complete_if_rated(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.DELIVERED)

        Rating.objects.create(
            booking=booking, reviewer=self.driver, reviewed_user=self.sender, score=4,
        )
        services.complete_if_rated(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)
        self.transport_request.refresh_from_db()
        self.assertEqual(self.transport_request.status, TransportRequest.Status.COMPLETED)

        # Chaufførens rating kan nu ses på profilen.
        self.assertEqual(self.driver.average_rating, 5.0)

    def test_decline_flow(self):
        booking = services.create_booking_request(self.match)
        services.decline_booking(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, Match.Status.DECLINED)

    def test_cannot_request_same_match_twice(self):
        services.create_booking_request(self.match)
        self.match.refresh_from_db()
        with self.assertRaises(services.BookingError):
            services.create_booking_request(self.match)

    def test_only_participants_can_view_booking(self):
        booking = services.create_booking_request(self.match)
        outsider = User.objects.create_user("nysgerrig", password="x")
        self.client.force_login(outsider)
        response = self.client.get(booking.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        self.client.force_login(self.sender)
        response = self.client.get(booking.get_absolute_url())
        self.assertEqual(response.status_code, 200)
