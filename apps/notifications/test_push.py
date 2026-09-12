import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from pywebpush import WebPushException

from apps.bookings import services as booking_services
from apps.matching.services import MatchingService
from apps.matching.tests import make_request, make_trip

from . import push
from .models import PushConfig, PushSubscription

User = get_user_model()

SUBSCRIPTION = {
    "endpoint": "https://push.example.com/abc123",
    "keys": {"p256dh": "testkey", "auth": "testauth"},
}


class PushConfigTests(TestCase):
    def test_config_is_generated_once(self):
        first = push.get_push_config()
        second = push.get_push_config()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(PushConfig.objects.count(), 1)
        self.assertIn("BEGIN PRIVATE KEY", first.private_key_pem)
        # Application server key: 65 bytes ukomprimeret punkt i base64.
        self.assertEqual(len(first.public_key), 87)
        self.assertNotIn("=", first.public_key)


class SubscriptionEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jesper", password="x")
        self.client.force_login(self.user)

    def test_subscribe_and_unsubscribe(self):
        response = self.client.post(
            "/notifikationer/subscribe/",
            json.dumps(SUBSCRIPTION),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        subscription = PushSubscription.objects.get()
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.endpoint, SUBSCRIPTION["endpoint"])

        response = self.client.post(
            "/notifikationer/unsubscribe/",
            json.dumps({"endpoint": SUBSCRIPTION["endpoint"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_invalid_payload_rejected(self):
        response = self.client.post(
            "/notifikationer/subscribe/", "ikke json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_vapid_endpoint_returns_key(self):
        response = self.client.get("/notifikationer/vapid/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("publicKey", response.json())


class SendPushTests(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user("martin", password="x")
        self.sender = User.objects.create_user("jesper", password="x")
        PushSubscription.objects.create(
            user=self.sender, endpoint=SUBSCRIPTION["endpoint"],
            p256dh="k", auth="a",
        )

    def test_booking_accept_sends_push_to_customer(self):
        make_trip(self.driver, "Kolding", "Sønderborg")
        transport_request = make_request(self.sender, "Kolding", "Aabenraa")
        MatchingService().find_matches_for_request(transport_request)
        booking = booking_services.create_booking_request(
            transport_request.matches.first()
        )
        with patch.object(push, "_deliver") as deliver:
            booking_services.accept_booking(booking)
        self.assertEqual(deliver.call_count, 1)
        payload = json.loads(deliver.call_args.args[1])
        self.assertIn("accepteret", payload["title"].lower())
        self.assertIn("/bookinger/", payload["url"])

    def test_dead_subscription_is_pruned(self):
        error = WebPushException("borte")
        error.response = type("Response", (), {"status_code": 410})()
        with patch.object(push, "_deliver", side_effect=error):
            delivered = push.send_push(self.sender, "Test", "Krop")
        self.assertEqual(delivered, 0)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_no_subscriptions_is_a_noop(self):
        with patch.object(push, "_deliver") as deliver:
            delivered = push.send_push(self.driver, "Test", "Krop")
        self.assertEqual(delivered, 0)
        deliver.assert_not_called()


class PwaEndpointTests(TestCase):
    def test_service_worker_and_manifest_serve(self):
        response = self.client.get("/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertIn(b"showNotification", response.content)
        self.assertIn(b"/offline/", response.content)

        response = self.client.get("/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "PåVejen")
        icon_sources = [icon["src"] for icon in data["icons"]]
        self.assertIn("/static/img/icon-192.png", icon_sources)
        self.assertIn("/static/img/icon-maskable-512.png", icon_sources)
        purposes = {icon["purpose"] for icon in data["icons"]}
        self.assertIn("maskable", purposes)

    def test_offline_page_serves(self):
        response = self.client.get("/offline/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Du er offline")
