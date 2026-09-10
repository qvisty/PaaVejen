from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bookings import services as booking_services
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip
from apps.transport.models import TransportRequest
from apps.trips.models import Trip

from .models import Payment

User = get_user_model()


class PaymentAndDisputeTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user("martin", password="x")
        self.sender = User.objects.create_user("jesper", password="x")
        self.trip = make_trip(self.driver, "Kolding", "Sønderborg")
        self.request = make_request(self.sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(self.request)
        self.booking = booking_services.create_booking_request(
            self.request.matches.first()
        )

    def test_payment_reserved_on_accept_and_released_on_delivery(self):
        booking_services.accept_booking(self.booking)
        payment = self.booking.payment
        self.assertEqual(payment.status, Payment.Status.RESERVED)
        self.assertEqual(payment.amount, self.booking.agreed_price)
        self.assertEqual(
            payment.amount, payment.platform_fee + payment.driver_payout,
        )
        # 15 % gebyr, jf. PRD afsnit 13.
        self.assertEqual(payment.platform_fee, round(payment.amount * 0.15))

        booking_services.confirm_pickup(self.booking, self.booking.pickup_code)
        booking_services.confirm_delivery(self.booking, self.booking.delivery_code)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.RELEASED)
        self.assertIsNotNone(payment.released_at)

    def test_dispute_holds_payment(self):
        booking_services.accept_booking(self.booking)
        booking_services.open_dispute(self.booking, self.sender, "Varen er beskadiget.")

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "disputed")
        payment = self.booking.payment
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.ON_HOLD)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, TransportRequest.Status.DISPUTED)

    def test_dispute_requires_active_booking(self):
        with self.assertRaises(booking_services.BookingError):
            booking_services.open_dispute(self.booking, self.sender, "For tidligt.")

    def test_cancel_accepted_booking_reopens_trip_and_request(self):
        booking_services.accept_booking(self.booking)
        booking_services.cancel_booking(self.booking, self.driver)

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")
        payment = self.booking.payment
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CANCELLED)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, Trip.Status.ACTIVE)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, TransportRequest.Status.MATCHED)

    def test_cannot_cancel_after_pickup(self):
        booking_services.accept_booking(self.booking)
        booking_services.confirm_pickup(self.booking, self.booking.pickup_code)
        with self.assertRaises(booking_services.BookingError):
            booking_services.cancel_booking(self.booking, self.sender)
