"""
Prisforslag, jf. PRD afsnit 12.

Princippet er kompensation for besvær og ekstraomkostninger:
grundbeløb + omvej + tid + størrelse.
"""
from django.conf import settings


def suggest_price(detour_km: float, detour_minutes: float, size: str) -> int:
    cfg = settings.PAAVEJEN
    price = (
        cfg["PRICE_BASE"]
        + detour_km * cfg["PRICE_PER_DETOUR_KM"]
        + detour_minutes * cfg["PRICE_PER_DETOUR_MIN"]
        + cfg["PRICE_SIZE_SUPPLEMENT"].get(size, 0)
    )
    # Afrund til nærmeste 5 kr., så prisen føles enkel.
    return int(round(price / 5.0) * 5)
