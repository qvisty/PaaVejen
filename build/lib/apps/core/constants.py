"""Fælles domænekonstanter for PåVejen."""

# Størrelses- og kapacitetsskala, jf. PRD afsnit 9 (Flow A).
# Samme skala bruges for varens størrelse og bilens ledige kapacitet,
# så de kan sammenlignes direkte.
SIZE_SMALL_BAG = "small_bag"
SIZE_MOVING_BOX = "moving_box"
SIZE_SEVERAL_BOXES = "several_boxes"
SIZE_TRUNK = "trunk"
SIZE_STATION_WAGON = "station_wagon"
SIZE_VAN = "van"
SIZE_TRAILER = "trailer"

SIZE_CHOICES = [
    (SIZE_SMALL_BAG, "Lille taske"),
    (SIZE_MOVING_BOX, "Flyttekasse"),
    (SIZE_SEVERAL_BOXES, "Flere kasser"),
    (SIZE_TRUNK, "Bagagerum"),
    (SIZE_STATION_WAGON, "Stationcar"),
    (SIZE_VAN, "Varebil"),
    (SIZE_TRAILER, "Trailer"),
]

# Rangorden til kapacitetssammenligning. Højere tal betyder mere plads.
SIZE_ORDER = {key: index for index, (key, _label) in enumerate(SIZE_CHOICES)}


# Forbudte genstande, jf. PRD afsnit 19. Vises i vilkårene og bekræftes
# ved oprettelse af transportopgaver.
FORBIDDEN_ITEMS = [
    "Våben, ammunition og eksplosiver",
    "Ulovlige stoffer",
    "Receptpligtig medicin",
    "Farligt gods, fx brandfarlige væsker og gasser",
    "Levende dyr",
    "Kontanter og værdipapirer",
    "Varer med en værdi over 5.000 kr.",
    "Alkohol og andre regulerede varer",
    "Varer med ulovligt indhold",
]


def size_fits(item_size: str, vehicle_capacity: str) -> bool:
    """Kan en vare af item_size være i en bil med vehicle_capacity?"""
    return SIZE_ORDER.get(vehicle_capacity, -1) >= SIZE_ORDER.get(item_size, 0)
