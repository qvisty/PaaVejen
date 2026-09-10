"""
Geografiske hjælpefunktioner.

Prototypen bruger luftlinjegeometri. Når produktet modnes, erstattes
beregningerne af en rigtig routing API via apps.core.routing, jf. PRD
afsnit 11 og 33.
"""
import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class Point:
    lat: float
    lng: float


def haversine_km(a: Point, b: Point) -> float:
    """Luftlinjeafstand i kilometer mellem to punkter."""
    lat1, lng1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lng2 = math.radians(b.lat), math.radians(b.lng)
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _project_to_plane(point: Point, ref_lat: float) -> tuple[float, float]:
    """Ekvirektangulær projektion til et lokalt km plan. Fint til Danmark."""
    x = math.radians(point.lng) * math.cos(math.radians(ref_lat)) * EARTH_RADIUS_KM
    y = math.radians(point.lat) * EARTH_RADIUS_KM
    return x, y


def point_to_segment(point: Point, seg_start: Point, seg_end: Point) -> tuple[float, float]:
    """
    Afstand fra et punkt til linjestykket mellem seg_start og seg_end.

    Returnerer (afstand_km, t) hvor t i [0, 1] angiver hvor på
    linjestykket det nærmeste punkt ligger. t bruges til at afgøre om
    afhentning kommer før aflevering langs ruten.
    """
    ref_lat = (seg_start.lat + seg_end.lat) / 2
    px, py = _project_to_plane(point, ref_lat)
    ax, ay = _project_to_plane(seg_start, ref_lat)
    bx, by = _project_to_plane(seg_end, ref_lat)

    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay), 0.0

    t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), t


# Simpelt opslagsværk til prototypen, så brugere kan nøjes med at skrive
# et bynavn. Erstattes senere af rigtig geocoding, jf. PRD afsnit 33.
KNOWN_PLACES = {
    "aabenraa": Point(55.0443, 9.4174),
    "aalborg": Point(57.0488, 9.9217),
    "aarhus": Point(56.1629, 10.2039),
    "billund": Point(55.7308, 9.1153),
    "esbjerg": Point(55.4765, 8.4594),
    "fredericia": Point(55.5657, 9.7527),
    "haderslev": Point(55.2494, 9.4894),
    "herning": Point(56.1393, 8.9738),
    "horsens": Point(55.8607, 9.8503),
    "kolding": Point(55.4904, 9.4722),
    "københavn": Point(55.6761, 12.5683),
    "middelfart": Point(55.5060, 9.7305),
    "nyborg": Point(55.3122, 10.7896),
    "odense": Point(55.4038, 10.4024),
    "padborg": Point(54.8259, 9.3592),
    "randers": Point(56.4607, 10.0364),
    "ribe": Point(55.3282, 8.7620),
    "roskilde": Point(55.6415, 12.0803),
    "silkeborg": Point(56.1697, 9.5451),
    "skanderborg": Point(56.0400, 9.9316),
    "slagelse": Point(55.4027, 11.3546),
    "sønderborg": Point(54.9093, 9.7920),
    "tønder": Point(54.9331, 8.8639),
    "vejle": Point(55.7090, 9.5357),
    "vojens": Point(55.2464, 9.3068),
}


def lookup_place(name: str) -> Point | None:
    """Slå et kendt dansk bynavn op. Returnerer None hvis ukendt."""
    if not name:
        return None
    return KNOWN_PLACES.get(name.strip().lower())
