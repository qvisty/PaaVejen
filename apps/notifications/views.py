import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import PushSubscription
from .push import get_push_config


@login_required
def vapid_public_key(request):
    return JsonResponse({"publicKey": get_push_config().public_key})


@login_required
@require_POST
def subscribe(request):
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh, auth = keys["p256dh"], keys["auth"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({"error": "Ugyldigt abonnement."}, status=400)
    if len(endpoint) > 500:
        return JsonResponse({"error": "Endpoint er for langt."}, status=400)
    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": request.user, "p256dh": p256dh, "auth": auth},
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({"error": "Ugyldigt endpoint."}, status=400)
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


def service_worker(request):
    """Service worker fra roden, så den kan styre hele sitet."""
    js = render_to_string("notifications/sw.js")
    return HttpResponse(js, content_type="application/javascript")


def manifest(request):
    """Webmanifest, så PåVejen kan installeres som PWA, jf. PRD fase 4."""
    data = {
        "id": "/",
        "name": "PåVejen",
        "short_name": "PåVejen",
        "description": "Match ture med ting, der skal samme vej.",
        "lang": "da",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7f6f3",
        "theme_color": "#1f6f5c",
        "icons": [
            {"src": "/static/img/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/static/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/static/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
            {"src": "/static/img/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")
