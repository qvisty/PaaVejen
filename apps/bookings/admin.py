from django.contrib import admin

from . import services
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer", "driver", "agreed_price", "status",
        "created_at", "collected_at", "delivered_at",
    )
    list_filter = ("status",)
    search_fields = ("customer__username", "driver__username")
    actions = ["resolve_refund", "resolve_release"]

    @admin.action(description="Afgør konflikt: refundér til afsenderen")
    def resolve_refund(self, request, queryset):
        self._resolve(request, queryset, "refund")

    @admin.action(description="Afgør konflikt: frigiv til chaufføren")
    def resolve_release(self, request, queryset):
        self._resolve(request, queryset, "release")

    def _resolve(self, request, queryset, resolution):
        resolved = 0
        skipped = 0
        for booking in queryset:
            try:
                services.resolve_dispute(booking, resolution, by_admin=request.user)
                resolved += 1
            except services.BookingError:
                skipped += 1
        if resolved:
            self.message_user(request, f"{resolved} konflikt(er) afgjort.")
        if skipped:
            self.message_user(
                request,
                f"{skipped} booking(er) sprunget over, da de ikke er i konflikt.",
                level="warning",
            )
