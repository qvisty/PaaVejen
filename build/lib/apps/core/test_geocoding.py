from django.test import TestCase

from .geocoding import ChainGeocoder, DawaGeocoder, LocalGeocoder, get_geocoder


class LocalGeocoderTests(TestCase):
    def test_known_city(self):
        result = LocalGeocoder().geocode("Kolding")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.point.lat, 55.4904, places=3)

    def test_unknown_place(self):
        self.assertIsNone(LocalGeocoder().geocode("Atlantis"))


class FakeFetch:
    """Simulerer DAWA svar uden netværk."""

    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        for fragment, response in self.responses.items():
            if fragment in url:
                return response
        return None


class DawaGeocoderTests(TestCase):
    def test_address_lookup(self):
        fetch = FakeFetch({
            "/adgangsadresser": [
                {"betegnelse": "Storegade 12, 6200 Aabenraa", "x": "9.4174", "y": "55.0443"},
            ],
        })
        result = DawaGeocoder(fetch=fetch).geocode("Storegade 12, Aabenraa")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "Storegade 12, 6200 Aabenraa")
        self.assertAlmostEqual(result.point.lat, 55.0443)
        # Forespørgsler med husnummer prøver adressesøgningen først.
        self.assertIn("/adgangsadresser", fetch.urls[0])

    def test_city_lookup(self):
        fetch = FakeFetch({
            "/postnumre": [
                {"navn": "Rødekro", "visueltcenter": [9.3392, 55.0704]},
            ],
        })
        result = DawaGeocoder(fetch=fetch).geocode("Rødekro")
        self.assertIsNotNone(result)
        self.assertEqual(result.display_name, "Rødekro")
        self.assertAlmostEqual(result.point.lat, 55.0704)
        # Rene bynavne prøver postnummersøgningen først.
        self.assertIn("/postnumre", fetch.urls[0])

    def test_network_failure_returns_none(self):
        result = DawaGeocoder(fetch=lambda url: None).geocode("Rødekro")
        self.assertIsNone(result)

    def test_malformed_response_returns_none(self):
        fetch = FakeFetch({"/postnumre": [{"navn": "X"}], "/adgangsadresser": [{}]})
        self.assertIsNone(DawaGeocoder(fetch=fetch).geocode("X"))

    def test_empty_query_returns_none(self):
        self.assertIsNone(DawaGeocoder(fetch=lambda url: []).geocode("  "))


class ChainGeocoderTests(TestCase):
    def test_local_hit_skips_dawa(self):
        fetch = FakeFetch({})
        chain = ChainGeocoder([LocalGeocoder(), DawaGeocoder(fetch=fetch)])
        result = chain.geocode("Kolding")
        self.assertIsNotNone(result)
        self.assertEqual(fetch.urls, [])

    def test_falls_through_to_dawa(self):
        fetch = FakeFetch({
            "/postnumre": [{"navn": "Rødekro", "visueltcenter": [9.3392, 55.0704]}],
        })
        chain = ChainGeocoder([LocalGeocoder(), DawaGeocoder(fetch=fetch)])
        result = chain.geocode("Rødekro")
        self.assertIsNotNone(result)
        self.assertGreater(len(fetch.urls), 0)

    def test_factory_builds_chain(self):
        self.assertIsInstance(get_geocoder(), ChainGeocoder)
