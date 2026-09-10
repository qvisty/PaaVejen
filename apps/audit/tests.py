from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bookings import services as booking_services
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip

from .models import AuditEvent

User = get_user_model()


class AuditTrailTests(TestCase):
    def test_booking_flow_is_logged(self):
        driver = User.objects.create_user("martin", password="x")
        sender = User.objects.create_user("jesper", password="x")
        make_trip(driver, "Kolding", "Sønderborg")
        transport_request = make_request(sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(transport_request)

        booking = booking_services.create_booking_request(
            transport_request.matches.first()
        )
        booking_services.accept_booking(booking)
        booking_services.confirm_pickup(booking, booking.pickup_code)
        booking_services.confirm_delivery(booking, booking.delivery_code)

        events = list(
            AuditEvent.objects.filter(booking=booking)
            .order_by("timestamp")
            .values_list("event_type", flat=True)
        )
        self.assertEqual(
            events,
            [
                "booking_requested",
                "booking_accepted",
                "payment_reserved",
                "pickup_confirmed",
                "payment_released",
                "delivery_confirmed",
            ],
        )
