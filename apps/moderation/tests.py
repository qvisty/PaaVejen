from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.matching.tests import make_request

from .models import Report

User = get_user_model()


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
