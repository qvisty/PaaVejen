"""
Web push, jf. PRD afsnit 22.

VAPID nøgleparret genereres første gang, der er brug for det, og gemmes
i databasen, så driften ikke kræver nøgleopsætning. Afsendelse må
aldrig vælte den handling, der udløste notifikationen, og døde
abonnementer ryddes op, når push tjenesten afviser dem.
"""
import base64
import json
import logging

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import WebPushException, webpush

from .models import PushConfig, PushSubscription

logger = logging.getLogger(__name__)

VAPID_CLAIM_EMAIL = "mailto:noreply@paavejen.dk"


def get_push_config() -> PushConfig:
    config = PushConfig.objects.first()
    if config is not None:
        return config
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_point = private_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    public_key = base64.urlsafe_b64encode(public_point).rstrip(b"=").decode()
    return PushConfig.objects.create(
        private_key_pem=private_pem, public_key=public_key,
    )


def _deliver(subscription: PushSubscription, payload: str, config: PushConfig):
    """Selve leveringen, adskilt så den kan erstattes i tests."""
    webpush(
        subscription_info={
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        },
        data=payload,
        vapid_private_key=config.private_key_pem,
        vapid_claims={"sub": VAPID_CLAIM_EMAIL},
    )


def send_push(user, title: str, body: str, url: str | None = None) -> int:
    """Send en push notifikation til alle brugerens enheder.

    Returnerer antal leverede. Fejl logges og vælter aldrig kaldet.
    """
    subscriptions = list(user.push_subscriptions.all())
    if not subscriptions:
        return 0
    try:
        config = get_push_config()
    except Exception:
        logger.exception("Kunne ikke hente push konfiguration")
        return 0
    payload = json.dumps({"title": title, "body": body, "url": url or "/"})
    delivered = 0
    for subscription in subscriptions:
        try:
            _deliver(subscription, payload, config)
            delivered += 1
        except WebPushException as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            if status in (404, 410):
                # Abonnementet findes ikke længere hos push tjenesten.
                subscription.delete()
            else:
                logger.warning("Push fejlede for %s: %s", user, error)
        except Exception:
            logger.exception("Uventet push fejl for %s", user)
    return delivered
