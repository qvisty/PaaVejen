from django.test import TestCase

from .constants import SIZE_MOVING_BOX, SIZE_SMALL_BAG, SIZE_TRAILER, size_fits
from .geo import Point, haversine_km, lookup_place, point_to_segment
from .pricing import suggest_price
from .routing import StraightLineRouter

KOLDING = Point(55.4904, 9.4722)
AABENRAA = Point(55.0443, 9.4174)
KOEBENHAVN = Point(55.6761, 12.5683)


class GeoTests(TestCase):
    def test_haversine_kolding_aabenraa(self):
        distance = haversine_km(KOLDING, AABENRAA)
        # Luftlinjen er cirka 50 km.
        self.assertGreater(distance, 40)
        self.assertLess(distance, 60)

    def test_point_on_segment_has_small_offset(self):
        haderslev = lookup_place("Haderslev")
        offset, t = point_to_segment(haderslev, KOLDING, AABENRAA)
        self.assertLess(offset, 10)
        self.assertGreater(t, 0.0)
        self.assertLess(t, 1.0)

    def test_point_far_from_segment(self):
        offset, _t = point_to_segment(KOEBENHAVN, KOLDING, AABENRAA)
        self.assertGreater(offset, 100)

    def test_lookup_place_is_case_insensitive(self):
        self.assertIsNotNone(lookup_place("kolding"))
        self.assertIsNotNone(lookup_place("Kolding "))
        self.assertIsNone(lookup_place("Atlantis"))


class RoutingTests(TestCase):
    def test_estimate_via_sums_legs(self):
        router = StraightLineRouter()
        direct = router.estimate(KOLDING, AABENRAA)
        via = router.estimate_via([KOLDING, lookup_place("Haderslev"), AABENRAA])
        self.assertGreaterEqual(via.distance_km, direct.distance_km)


class PricingTests(TestCase):
    def test_price_grows_with_detour_and_size(self):
        small = suggest_price(2, 5, SIZE_SMALL_BAG)
        big = suggest_price(20, 25, SIZE_TRAILER)
        self.assertGreater(big, small)

    def test_price_rounded_to_five(self):
        price = suggest_price(3.7, 6.2, SIZE_MOVING_BOX)
        self.assertEqual(price % 5, 0)


class CapacityTests(TestCase):
    def test_size_fits(self):
        self.assertTrue(size_fits(SIZE_SMALL_BAG, SIZE_TRAILER))
        self.assertTrue(size_fits(SIZE_MOVING_BOX, SIZE_MOVING_BOX))
        self.assertFalse(size_fits(SIZE_TRAILER, SIZE_SMALL_BAG))
