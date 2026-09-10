"""
Routingabstraktion, jf. PRD afsnit 11.

Prototypen bruger en luftlinjebaseret estimator. Interfacet er designet,
så en rigtig udbyder (Google Maps, Mapbox, HERE, OpenRouteService) senere
kan sættes ind uden ændringer i matchingmotoren.
"""
from dataclasses import dataclass

from .geo import Point, haversine_km


@dataclass(frozen=True)
class RouteEstimate:
    distance_km: float
    duration_minutes: float


class BaseRouter:
    def estimate(self, origin: Point, destination: Point) -> RouteEstimate:
        raise NotImplementedError

    def estimate_via(self, waypoints: list[Point]) -> RouteEstimate:
        """Samlet estimat for en rute gennem alle waypoints i rækkefølge."""
        total_km = 0.0
        total_min = 0.0
        for start, end in zip(waypoints, waypoints[1:]):
            leg = self.estimate(start, end)
            total_km += leg.distance_km
            total_min += leg.duration_minutes
        return RouteEstimate(total_km, total_min)


class StraightLineRouter(BaseRouter):
    """
    Estimerer vejafstand som luftlinje gange en vejfaktor, og køretid ud
    fra en gennemsnitshastighed. Groft, men nok til at teste
    matchingoplevelsen, jf. PRD afsnit 40.
    """

    ROAD_FACTOR = 1.3
    AVERAGE_SPEED_KMH = 70.0

    def estimate(self, origin: Point, destination: Point) -> RouteEstimate:
        distance_km = haversine_km(origin, destination) * self.ROAD_FACTOR
        duration_minutes = distance_km / self.AVERAGE_SPEED_KMH * 60.0
        return RouteEstimate(distance_km, duration_minutes)


def get_router() -> BaseRouter:
    """Central fabrik, så udbyderen kan udskiftes ét sted."""
    return StraightLineRouter()
