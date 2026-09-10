"""
Geocoding, jf. PRD afsnit 33.

Prototypen bruger DAWA, Danmarks Adressers Web API fra Dataforsyningen.
Tjenesten er gratis og kræver ingen nøgle. Opslag går først til det
lokale opslagsværk over kendte byer, som er hurtigt og virker offline,
og derefter til DAWA for rigtige adresser og øvrige stednavne.

Abstraktionen gør det muligt senere at skifte udbyder ét sted.
"""
import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .geo import Point, lookup_place

logger = logging.getLogger(__name__)

DAWA_BASE_URL = "https://api.dataforsyningen.dk"
REQUEST_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class GeocodeResult:
    display_name: str
    point: Point


def _default_fetch(url: str):
    """Hent og parse JSON. Returnerer None ved enhver fejl."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "PaaVejen/0.1"})
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except Exception:
        logger.warning("Geocoding opslag fejlede: %s", url, exc_info=True)
        return None


class BaseGeocoder:
    def geocode(self, query: str) -> GeocodeResult | None:
        raise NotImplementedError


class LocalGeocoder(BaseGeocoder):
    """Opslagsværk over kendte danske byer. Hurtigt og offline."""

    def geocode(self, query: str) -> GeocodeResult | None:
        point = lookup_place(query)
        if point is None:
            return None
        return GeocodeResult(display_name=query.strip(), point=point)


class DawaGeocoder(BaseGeocoder):
    """
    Slår adresser og bynavne op i DAWA.

    Forespørgsler med husnummer rammer adressesøgningen, rene bynavne
    rammer postnummersøgningen. Begge forsøges, mest sandsynlige først.
    """

    def __init__(self, fetch=None):
        self.fetch = fetch or _default_fetch

    def geocode(self, query: str) -> GeocodeResult | None:
        query = (query or "").strip()
        if not query:
            return None
        looks_like_address = any(char.isdigit() for char in query)
        lookups = [self._geocode_address, self._geocode_city]
        if not looks_like_address:
            lookups.reverse()
        for lookup in lookups:
            result = lookup(query)
            if result is not None:
                return result
        return None

    def _geocode_address(self, query: str) -> GeocodeResult | None:
        url = (
            f"{DAWA_BASE_URL}/adgangsadresser?q={urllib.parse.quote(query)}"
            "&per_side=1&struktur=mini"
        )
        data = self.fetch(url)
        if not data:
            return None
        first = data[0]
        try:
            return GeocodeResult(
                display_name=first["betegnelse"],
                point=Point(float(first["y"]), float(first["x"])),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _geocode_city(self, query: str) -> GeocodeResult | None:
        url = f"{DAWA_BASE_URL}/postnumre?q={urllib.parse.quote(query)}"
        data = self.fetch(url)
        if not data:
            return None
        first = data[0]
        try:
            lng, lat = first["visueltcenter"]
            return GeocodeResult(
                display_name=first["navn"],
                point=Point(float(lat), float(lng)),
            )
        except (KeyError, TypeError, ValueError):
            return None


class ChainGeocoder(BaseGeocoder):
    """Prøver flere geocodere i rækkefølge."""

    def __init__(self, geocoders: list[BaseGeocoder]):
        self.geocoders = geocoders

    def geocode(self, query: str) -> GeocodeResult | None:
        for geocoder in self.geocoders:
            result = geocoder.geocode(query)
            if result is not None:
                return result
        return None


def get_geocoder() -> BaseGeocoder:
    """Central fabrik, så udbyderen kan udskiftes ét sted."""
    return ChainGeocoder([LocalGeocoder(), DawaGeocoder()])
