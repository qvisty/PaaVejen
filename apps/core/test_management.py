from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.bookings import services as booking_services
from apps.bookings.models import Booking
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip
from apps.payments.models import Payment

User = get_user_model()


class EnsureSuperuserTests(TestCase):
    def test_creates_superuser_from_env(self):
        env = {
            "DJANGO_SUPERUSER_USERNAME": "chef",
            "DJANGO_SUPERUSER_PASSWORD": "hemmelig-kode-123",
            "DJANGO_SUPERUSER_EMAIL": "chef@example.com",
        }
        with self.settings():
            import os
            old = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                call_command("ensure_superuser")
                user = User.objects.get(username="chef")
                self.assertTrue(user.is_superuser)

                # Idempotent: kør igen, og rør ikke ved kodeordet.
                user.set_password("nyt-kodeord-456")
                user.save()
                call_command("ensure_superuser")
                user.refresh_from_db()
                self.assertTrue(user.check_password("nyt-kodeord-456"))
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_skips_without_env(self):
        call_command("ensure_superuser")
        self.assertEqual(User.objects.count(), 0)


class CleanupDemoUsersTests(TestCase):
    def test_deletes_demo_users_with_bookings(self):
        demo_driver = User.objects.create_user("demo-martin-123456", password="x")
        demo_sender = User.objects.create_user("demo-jesper-123456", password="x")
        real_user = User.objects.create_user("demo-uden-tidsstempel", password="x")

        make_trip(demo_driver, "Kolding", "Sønderborg")
        transport_request = make_request(demo_sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(transport_request)
        booking = booking_services.create_booking_request(
            transport_request.matches.first()
        )
        booking_services.accept_booking(booking)

        call_command("cleanup_demo_users")

        self.assertFalse(User.objects.filter(username__regex=r"^demo-[a-z]+-\d{6}$").exists())
        self.assertTrue(User.objects.filter(username="demo-uden-tidsstempel").exists())
        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
