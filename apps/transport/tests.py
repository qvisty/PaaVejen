from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class RequestFormTests(TestCase):
    def test_category_explainers_are_shown(self):
        user = User.objects.create_user("t", password="x")
        self.client.force_login(user)
        response = self.client.get("/opgaver/ny/")
        html = response.content.decode()
        self.assertIn("Tag med", html)
        self.assertIn("Hent for mig", html)
        self.assertIn("Aflever for mig", html)
        self.assertIn("købt på DBA", html)
        self.assertIn("category-illustration", html)
        self.assertIn("anim-car", html)
        self.assertIn("Click &amp; Collect", html)
        self.assertIn("returnering til en butik", html)
        # Standardvalget Tag med er markeret på forhånd.
        self.assertIn("checked", html)
