from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.matching.tests import make_request

from .models import Report
from .services import screen_text, screen_transport_request

User = get_user_model()


class ScreeningTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("ejer", password="x")

    def test_clean_text_passes(self):
        self.assertEqual(screen_text("En stol købt på DBA."), [])
        # Ordgrænser: "spiller" må ikke matche "piller", "hunden" ikke "hund".
        self.assertEqual(screen_text("En spiller til stereoanlægget til hunden."), [])

    def test_suspicious_text_is_categorized(self):
        hits = screen_text("En kasse patroner og lidt kontanter.")
        self.assertIn("våben", hits)
        self.assertIn("kontanter", hits)

    def test_suspicious_request_is_auto_flagged(self):
        transport_request = make_request(
            self.owner, "Kolding", "Aabenraa",
            description="En pistol, der skal til en samler.",
        )
        report = screen_transport_request(transport_request)
        self.assertIsNotNone(report)
        self.assertEqual(report.source, Report.Source.AUTO)
        self.assertIsNone(report.reporter)
        self.assertIn("våben", report.reason)

    def test_flagging_is_not_duplicated(self):
        transport_request = make_request(
            self.owner, "Kolding", "Aabenraa", description="En pistol.",
        )
        first = screen_transport_request(transport_request)
        second = screen_transport_request(transport_request)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(Report.objects.count(), 1)

    def test_clean_request_is_not_flagged(self):
        transport_request = make_request(
            self.owner, "Kolding", "Aabenraa", description="En sofa.",
        )
        self.assertIsNone(screen_transport_request(transport_request))
        self.assertEqual(Report.objects.count(), 0)


class ReportTests(TestCase):
    def test_user_can_report_a_request(self):
        owner = User.objects.create_user("ejer", password="x")
        reporter = User.objects.create_user("martin", password="x")
        transport_request = make_request(owner, "Kolding", "Aabenraa")

        self.client.force_login(reporter)
        response = self.client.post(
            f"/rapporter/opgave/{transport_request.pk}/",
            {"reason": "Beskrivelsen nævner receptpligtig medicin."},
        )

        self.assertEqual(response.status_code, 302)
        report = Report.objects.get()
        self.assertEqual(report.reporter, reporter)
        self.assertEqual(report.transport_request, transport_request)
        self.assertEqual(report.status, Report.Status.OPEN)

    def test_empty_reason_is_rejected(self):
        owner = User.objects.create_user("ejer", password="x")
        reporter = User.objects.create_user("martin", password="x")
        transport_request = make_request(owner, "Kolding", "Aabenraa")

        self.client.force_login(reporter)
        self.client.post(f"/rapporter/opgave/{transport_request.pk}/", {"reason": " "})

        self.assertEqual(Report.objects.count(), 0)
