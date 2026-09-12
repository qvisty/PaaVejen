import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from apps.core.models import StoredFile

User = get_user_model()


def make_image_upload(name="stol.png", size=(2400, 1200), fmt="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 40, 40)).save(buffer, format=fmt)
    buffer.seek(0)
    buffer.name = name
    return buffer


class ImageUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jesper", password="x")
        self.client.force_login(self.user)

    def _create_request_with_image(self):
        deadline = timezone.now() + timedelta(days=3)
        return self.client.post("/opgaver/ny/", {
            "category": "bring_along",
            "pickup_name": "Kolding", "delivery_name": "Aabenraa",
            "latest_delivery": deadline.strftime("%Y-%m-%dT%H:%M"),
            "description": "En stol.", "size": "moving_box",
            "terms_accepted": "on",
            "image": make_image_upload(),
        })

    def test_image_is_stored_in_database_and_served(self):
        response = self._create_request_with_image()
        self.assertEqual(response.status_code, 302)

        stored = StoredFile.objects.get()
        self.assertEqual(stored.content_type, "image/jpeg")

        # Billedet er nedskaleret og genkodet til JPEG.
        picture = Image.open(io.BytesIO(bytes(stored.content)))
        self.assertEqual(picture.format, "JPEG")
        self.assertLessEqual(max(picture.size), 1600)

        # Og serveres via viewet med login.
        serve = self.client.get(f"/filer/{stored.name}")
        self.assertEqual(serve.status_code, 200)
        self.assertEqual(serve["Content-Type"], "image/jpeg")

        # Detaljesiden peger på den servede URL.
        from apps.transport.models import TransportRequest

        transport_request = TransportRequest.objects.get()
        detail = self.client.get(transport_request.get_absolute_url())
        self.assertContains(detail, f"/filer/{stored.name}")

    def test_serving_requires_login(self):
        self._create_request_with_image()
        stored = StoredFile.objects.get()
        self.client.logout()
        response = self.client.get(f"/filer/{stored.name}")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/konto/login/", response["Location"])

    def test_invalid_image_is_rejected(self):
        deadline = timezone.now() + timedelta(days=3)
        fake = io.BytesIO(b"ikke et billede")
        fake.name = "fil.png"
        response = self.client.post("/opgaver/ny/", {
            "category": "bring_along",
            "pickup_name": "Kolding", "delivery_name": "Aabenraa",
            "latest_delivery": deadline.strftime("%Y-%m-%dT%H:%M"),
            "description": "En stol.", "size": "moving_box",
            "terms_accepted": "on",
            "image": fake,
        })
        self.assertEqual(response.status_code, 200)
        # Djangos egen ImageField validering afviser filen først.
        self.assertContains(response, "billedfil")
        self.assertEqual(StoredFile.objects.count(), 0)
