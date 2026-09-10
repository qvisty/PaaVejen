"""
Automatisk screening af opgaver, jf. PRD afsnit 19 og 26.

Screeningen er et aktivt værn mod misbrug: opgaver, hvis tekst matcher
forbudte kategorier, flages automatisk til manuel gennemgang i admin.
Der blokeres bevidst ikke alene på automatik, jf. PRD afsnit 26, men
flaget lander som en åben rapport og i auditloggen, så administrator
kan reagere hurtigt.
"""
import re

from apps.audit.services import log

from .models import Report

# Nøgleord pr. forbudt kategori. Bevidst konservativ liste, der hellere
# flager lidt for meget end for lidt. Matches som hele ord.
SUSPICIOUS_KEYWORDS = {
    "våben": ["våben", "pistol", "riffel", "haglgevær", "ammunition", "patroner", "eksplosiv", "fyrværkeri"],
    "stoffer": ["hash", "skunk", "kokain", "amfetamin", "mdma", "ecstasy", "narko"],
    "medicin": ["medicin", "receptpligtig", "piller", "morfin", "ozempic"],
    "kontanter": ["kontanter", "pengeseddel", "pengesedler"],
    "dyr": ["hund", "kat", "hvalp", "killing", "kanin", "levende dyr"],
    "alkohol og tobak": ["spiritus", "vodka", "whisky", "cigaretter", "snus"],
}


def screen_text(text: str) -> list[str]:
    """Returnér de kategorier, teksten matcher. Tom liste hvis ren."""
    lowered = (text or "").lower()
    hits = []
    for category, keywords in SUSPICIOUS_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", lowered):
                hits.append(category)
                break
    return hits


def screen_transport_request(transport_request) -> Report | None:
    """Screen en opgave og opret en automatisk rapport ved match."""
    text = f"{transport_request.description} {transport_request.pickup_name} {transport_request.delivery_name}"
    categories = screen_text(text)
    if not categories:
        return None
    already_flagged = Report.objects.filter(
        transport_request=transport_request,
        source=Report.Source.AUTO,
        status=Report.Status.OPEN,
    ).exists()
    if already_flagged:
        return None
    report = Report.objects.create(
        reporter=None,
        source=Report.Source.AUTO,
        transport_request=transport_request,
        reason=(
            "Automatisk screening: beskrivelsen matcher kategorierne "
            f"{', '.join(categories)}. Kræver manuel gennemgang."
        ),
    )
    log(
        "auto_flagged",
        user=transport_request.owner,
        categories=categories,
        transport_request_id=transport_request.pk,
    )
    return report
