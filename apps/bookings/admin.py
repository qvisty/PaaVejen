from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer", "driver", "agreed_price", "status",
        "created_at", "collected_at", "delivered_at",
    )
    list_filter = ("status",)
    search_fields = ("customer__username", "driver__username")
