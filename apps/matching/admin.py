from django.contrib import admin

from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "id", "trip", "transport_request", "match_score",
        "detour_km", "detour_minutes", "suggested_price", "status",
    )
    list_filter = ("status",)
