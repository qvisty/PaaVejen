from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("konto/", include("apps.accounts.urls")),
    path("ture/", include("apps.trips.urls")),
    path("opgaver/", include("apps.transport.urls")),
    path("matches/", include("apps.matching.urls")),
    path("bookinger/", include("apps.bookings.urls")),
    path("beskeder/", include("apps.messaging.urls")),
    path("ratings/", include("apps.ratings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
