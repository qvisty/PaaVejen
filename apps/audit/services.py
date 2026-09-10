"""Central logfunktion, så alle apps logger ens."""
from .models import AuditEvent


def log(event_type: str, *, user=None, booking=None, **metadata) -> AuditEvent:
    return AuditEvent.objects.create(
        event_type=event_type, user=user, booking=booking, metadata=metadata,
    )
