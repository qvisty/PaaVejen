from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from apps.bookings import services as booking_services
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip
from apps.messaging.models import Message
from apps.notifications import services as notifications

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            "martin", email="martin@example.com", password="x",
        )
        self.sender = User.objects.create_user(
            "jesper", email="jesper@example.com", password="x",
        )

    def test_new_match_mails_both_parties(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        make_request(self.sender, "Kolding", "Aabenraa")
        mail.outbox = []

        transport_request = make_request(self.sender, "Kolding", "Haderslev")
        MatchingService().find_matches_for_request(transport_request)

        recipients = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(recipients, ["jesper@example.com", "martin@example.com"])
        subjects = " ".join(m.subject for m in mail.outbox)
        self.assertIn("match", subjects.lower())

    def test_rerun_does_not_mail_again(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        service = MatchingService()
        service.find_matches_for_request(transport_request)
        mail.outbox = []

        service.find_matches_for_request(transport_request)

        self.assertEqual(mail.outbox, [])

    def test_booking_flow_sends_mails(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(transport_request)
        match = transport_request.matches.first()

        mail.outbox = []
        booking = booking_services.create_booking_request(match)
        self.assertEqual(mail.outbox[-1].to, ["martin@example.com"])

        booking_services.accept_booking(booking)
        self.assertEqual(mail.outbox[-1].to, ["jesper@example.com"])

        booking_services.confirm_pickup(booking, booking.pickup_code)
        self.assertEqual(mail.outbox[-1].to, ["jesper@example.com"])

        mail.outbox = []
        booking_services.confirm_delivery(booking, booking.delivery_code)
        recipients = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(recipients, ["jesper@example.com", "martin@example.com"])

    def test_chat_message_mails_other_party(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(transport_request)
        booking = booking_services.create_booking_request(
            transport_request.matches.first()
        )

        mail.outbox = []
        message = Message.objects.create(
            booking=booking, sender=self.sender, content="Kan du tage den fredag?",
        )
        notifications.notify_new_message(message)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["martin@example.com"])
        self.assertIn("Kan du tage den fredag?", mail.outbox[0].body)

    def test_user_without_email_is_skipped(self):
        no_mail_user = User.objects.create_user("uden", password="x")
        make_trip(no_mail_user, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        mail.outbox = []

        MatchingService().find_matches_for_request(transport_request)

        # Kun afsenderen har e mail, så der sendes præcis én mail.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jesper@example.com"])
