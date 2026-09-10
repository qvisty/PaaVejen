"""Materialisering af gentagne ture, jf. PRD afsnit 23."""
from apps.trips.models import RecurringTrip, Trip


def materialize_recurring_trips(start, end, exclude_driver=None) -> list[Trip]:
    """
    Opret konkrete Trip forekomster for alle aktive gentagne ture i
    tidsvinduet [start, end]. Eksisterende forekomster genbruges, så
    funktionen kan kaldes så ofte, det passer.
    """
    recurring_trips = RecurringTrip.objects.filter(active=True)
    if exclude_driver is not None:
        recurring_trips = recurring_trips.exclude(driver=exclude_driver)

    created = []
    for recurring in recurring_trips:
        for departure in recurring.upcoming_departures(start, end):
            trip, was_created = Trip.objects.get_or_create(
                recurring_trip=recurring,
                departure_time=departure,
                defaults={
                    "driver": recurring.driver,
                    "origin_name": recurring.origin_name,
                    "origin_lat": recurring.origin_lat,
                    "origin_lng": recurring.origin_lng,
                    "destination_name": recurring.destination_name,
                    "destination_lat": recurring.destination_lat,
                    "destination_lng": recurring.destination_lng,
                    "max_detour_minutes": recurring.max_detour_minutes,
                    "capacity": recurring.capacity,
                },
            )
            if was_created:
                created.append(trip)
    return created
