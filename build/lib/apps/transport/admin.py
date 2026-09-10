from django.contrib import admin

from .models import TransportRequest


@admin.register(TransportRequest)
class TransportRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id", "owner", "category", "pickup_name", "delivery_name",
        "size", "latest_delivery", "estimated_value", "status",
    )
    list_filter = ("status", "category", "size")
    search_fields = ("pickup_name", "delivery_name", "description", "owner__username")
