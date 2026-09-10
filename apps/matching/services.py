"""
Matchingmotoren, jf. PRD afsnit 10 og 34.

Arbejdsgang for hver kandidat:
1. Filtrér på status, tidsvindue og kapacitet.
2. Geografisk prefiltering: ligger afhentning og aflevering tæt nok på
   rutens korridor, og kommer afhentning før aflevering langs ruten?
3. Beregn omvej via routingabstraktionen.
4. Afvis hvis omvejen overstiger chaufførens grænse.
5. Beregn vægtet matchscore og prisforslag.
6. Gem eller opdatér Match.

Vægte, jf. PRD afsnit 10: rute 40 %, tidspunkt 25 %, omvej 15 %,
kapacitet 10 %, brugerhistorik 10 %. Skal senere optimeres ud fra data.
"""
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.core import pricing
from apps.core.constants import SIZE_ORDER, size_fits
from apps.notifications import services as notifications
from apps.core.geo import haversine_km, point_to_segment
from apps.core.routing import get_router
from apps.transport.models import TransportRequest
from apps.trips.models import Trip
from apps.trips.services import materialize_recurring_trips

from .models import Match

WEIGHT_ROUTE = 0.40
WEIGHT_TIME = 0.25
WEIGHT_DETOUR = 0.15
WEIGHT_CAPACITY = 0.10
WEIGHT_HISTORY = 0.10

# Tidsslæk: en tur må afgå lidt før tidligste afhentning, fordi
# tidspunkterne er cirkaangivelser.
DEPARTURE_SLACK = timedelta(hours=2)


@dataclass
class MatchCandidate:
    trip: Trip
    transport_request: TransportRequest
    score: int
    detour_km: float
    detour_minutes: float
    suggested_price: int


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class MatchingService:
    def __init__(self, router=None):
        self.router = router or get_router()
        self.config = settings.PAAVEJEN

    # Offentligt API, jf. PRD afsnit 34.

    def find_matches_for_request(self, transport_request: TransportRequest) -> list[Match]:
        """Find aktive ture, der passer til en transportopgave."""
        if transport_request.status not in (
            TransportRequest.Status.PUBLISHED,
            TransportRequest.Status.MATCHED,
        ):
            return []
        # Gentagne ture materialiseres i opgavens tidsvindue, så de kan
        # matches som almindelige ture, jf. PRD afsnit 23.
        window_start = transport_request.earliest_pickup or timezone.now()
        materialize_recurring_trips(
            start=max(window_start - DEPARTURE_SLACK, timezone.now()),
            end=transport_request.latest_delivery,
            exclude_driver=transport_request.owner,
        )
        trips = (
            Trip.objects.filter(status=Trip.Status.ACTIVE)
            .exclude(driver=transport_request.owner)
            .filter(departure_time__lte=transport_request.latest_delivery)
        )
        if transport_request.earliest_pickup:
            trips = trips.filter(
                departure_time__gte=transport_request.earliest_pickup - DEPARTURE_SLACK
            )
        matches = []
        for trip in trips:
            candidate = self.evaluate_pair(trip, transport_request)
            if candidate:
                matches.append(self._store(candidate))
        self._update_request_status(transport_request)
        return matches

    def find_matches_for_trip(self, trip: Trip) -> list[Match]:
        """Find åbne transportopgaver langs en tur."""
        if trip.status != Trip.Status.ACTIVE:
            return []
        requests = (
            TransportRequest.objects.filter(
                status__in=[
                    TransportRequest.Status.PUBLISHED,
                    TransportRequest.Status.MATCHED,
                ],
                latest_delivery__gte=trip.departure_time,
            )
            .exclude(owner=trip.driver)
        )
        matches = []
        for transport_request in requests:
            candidate = self.evaluate_pair(trip, transport_request)
            if candidate:
                matches.append(self._store(candidate))
                self._update_request_status(transport_request)
        return matches

    def evaluate_pair(
        self, trip: Trip, transport_request: TransportRequest
    ) -> MatchCandidate | None:
        """Vurdér ét (tur, opgave) par. Returnerer None hvis parret ikke dur."""
        if not size_fits(transport_request.size, trip.capacity):
            return None
        if transport_request.earliest_pickup and (
            trip.departure_time < transport_request.earliest_pickup - DEPARTURE_SLACK
        ):
            return None
        if trip.departure_time > transport_request.latest_delivery:
            return None

        origin = trip.origin_point
        destination = trip.destination_point
        pickup = transport_request.pickup_point
        delivery = transport_request.delivery_point

        trip_km = haversine_km(origin, destination)
        if trip_km < 1.0:
            return None

        # Geografisk prefiltering: korridor omkring ruten.
        corridor_km = min(
            self.config["MAX_CORRIDOR_KM"], max(10.0, trip_km * 0.35)
        )
        pickup_offset_km, pickup_t = point_to_segment(pickup, origin, destination)
        delivery_offset_km, delivery_t = point_to_segment(delivery, origin, destination)
        if pickup_offset_km > corridor_km or delivery_offset_km > corridor_km:
            return None
        # Afhentning skal komme før aflevering langs kørselsretningen.
        if delivery_t < pickup_t:
            return None

        # Omvej: rute med stop minus direkte rute.
        direct = self.router.estimate(origin, destination)
        with_stops = self.router.estimate_via([origin, pickup, delivery, destination])
        detour_km = max(0.0, with_stops.distance_km - direct.distance_km)
        detour_minutes = max(0.0, with_stops.duration_minutes - direct.duration_minutes)

        max_detour = (
            trip.max_detour_minutes or self.config["DEFAULT_MAX_DETOUR_MINUTES"]
        )
        if detour_minutes > max_detour:
            return None

        # Kan varen nå frem inden deadline?
        arrival_estimate = trip.departure_time + timedelta(
            minutes=with_stops.duration_minutes
        )
        if arrival_estimate > transport_request.latest_delivery:
            return None

        score = self._score(
            trip=trip,
            transport_request=transport_request,
            trip_km=trip_km,
            pickup_offset_km=pickup_offset_km,
            delivery_offset_km=delivery_offset_km,
            detour_minutes=detour_minutes,
            max_detour=max_detour,
            arrival_estimate=arrival_estimate,
        )
        price = pricing.suggest_price(detour_km, detour_minutes, transport_request.size)
        return MatchCandidate(
            trip=trip,
            transport_request=transport_request,
            score=score,
            detour_km=round(detour_km, 1),
            detour_minutes=round(detour_minutes, 1),
            suggested_price=price,
        )

    # Interne hjælpere.

    def _score(
        self, *, trip, transport_request, trip_km, pickup_offset_km,
        delivery_offset_km, detour_minutes, max_detour, arrival_estimate,
    ) -> int:
        corridor_km = self.config["MAX_CORRIDOR_KM"]

        # Rute: hvor tæt ligger begge punkter på ruten?
        route_score = _clamp(
            1.0 - (pickup_offset_km + delivery_offset_km) / (2.0 * corridor_km)
        )

        # Tid: hvor stor margin er der til seneste aflevering?
        margin_hours = (
            transport_request.latest_delivery - arrival_estimate
        ).total_seconds() / 3600.0
        time_score = _clamp(margin_hours / 12.0)

        # Omvej: jo mindre af chaufførens accepterede omvej der bruges, jo bedre.
        detour_score = _clamp(1.0 - detour_minutes / max_detour) if max_detour else 0.0

        # Kapacitet: perfekt pasform er bedst, stor overkapacitet trækker lidt ned.
        gap = SIZE_ORDER[trip.capacity] - SIZE_ORDER[transport_request.size]
        capacity_score = _clamp(1.0 - 0.05 * gap, low=0.7)

        # Brugerhistorik: chaufførens rating, neutral score uden historik.
        avg_rating = trip.driver.average_rating
        history_score = _clamp(avg_rating / 5.0) if avg_rating else 0.8

        total = (
            WEIGHT_ROUTE * route_score
            + WEIGHT_TIME * time_score
            + WEIGHT_DETOUR * detour_score
            + WEIGHT_CAPACITY * capacity_score
            + WEIGHT_HISTORY * history_score
        )
        return int(round(total * 100))

    def _store(self, candidate: MatchCandidate) -> Match:
        match, created = Match.objects.update_or_create(
            trip=candidate.trip,
            transport_request=candidate.transport_request,
            defaults={
                "match_score": candidate.score,
                "detour_km": candidate.detour_km,
                "detour_minutes": candidate.detour_minutes,
                "suggested_price": candidate.suggested_price,
            },
        )
        # Rør ikke ved matches, der allerede er i et bookingforløb.
        if match.status in (Match.Status.DECLINED, Match.Status.EXPIRED):
            match.status = Match.Status.SUGGESTED
            match.save(update_fields=["status"])
        if created:
            notifications.notify_new_match(match)
        return match

    def _update_request_status(self, transport_request: TransportRequest) -> None:
        if transport_request.status != TransportRequest.Status.PUBLISHED:
            return
        has_matches = transport_request.matches.filter(
            status=Match.Status.SUGGESTED
        ).exists()
        if has_matches:
            transport_request.status = TransportRequest.Status.MATCHED
            transport_request.save(update_fields=["status"])
