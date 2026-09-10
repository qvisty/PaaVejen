from django.contrib import admin

from .models import RecurringTrip, Trip


@admin.register(RecurringTrip)
class RecurringTripAdmin(admin.ModelAdmin):
    list_display = (
        "id", "driver", "origin_name", "destination_name",
        "weekday_labels", "departure_time", "capacity", "active",
    )
    list_filter = ("active", "capacity")
    search_fields = ("origin_name", "destination_name", "driver__username")


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "id", "driver", "origin_name", "destination_name",
        "departure_time", "capacity", "max_detour_minutes", "status",
    )
    list_filter = ("status", "capacity")
    search_fields = ("origin_name", "destination_name", "driver__username")
