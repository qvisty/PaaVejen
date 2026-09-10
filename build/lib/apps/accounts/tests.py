from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SignupTermsTests(TestCase):
    def test_signup_requires_terms(self):
        data = {
            "username": "ny",
            "password1": "sikkerKode123",
            "password2": "sikkerKode123",
        }
        response = self.client.post("/konto/opret/", data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="ny").exists())

        data["accept_terms"] = "on"
        response = self.client.post("/konto/opret/", data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="ny")
        self.assertIsNotNone(user.terms_accepted_at)


class ProfileTests(TestCase):
    def test_profile_requires_login(self):
        response = self.client.get("/konto/profil/")
        self.assertEqual(response.status_code, 302)

    def test_profile_shows_and_updates(self):
        user = User.objects.create_user("jesper", password="x")
        self.client.force_login(user)

        response = self.client.get("/konto/profil/")
        self.assertContains(response, "Min profil")

        response = self.client.post(
            "/konto/profil/",
            {
                "first_name": "Jesper",
                "last_name": "Q",
                "email": "jesper@example.com",
                "phone": "12345678",
            },
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, "jesper@example.com")
        self.assertEqual(user.phone, "12345678")
