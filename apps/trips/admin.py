from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "id", "driver", "origin_name", "destination_name",
        "departure_time", "capacity", "max_detour_minutes", "status",
    )
    list_filter = ("status", "capacity")
    search_fields = ("origin_name", "destination_name", "driver__username")
