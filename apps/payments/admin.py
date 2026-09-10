from django.contrib import admin
from django.utils import timezone

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id", "booking", "amount", "platform_fee", "driver_payout",
        "provider", "status", "created_at", "released_at",
    )
    list_filter = ("status", "provider")
    actions = ["release_payments", "refund_payments"]

    @admin.action(description="Frigiv valgte betalinger")
    def release_payments(self, request, queryset):
        queryset.filter(
            status__in=[Payment.Status.RESERVED, Payment.Status.ON_HOLD]
        ).update(status=Payment.Status.RELEASED, released_at=timezone.now())

    @admin.action(description="Refundér valgte betalinger")
    def refund_payments(self, request, queryset):
        queryset.filter(
            status__in=[Payment.Status.RESERVED, Payment.Status.ON_HOLD]
        ).update(status=Payment.Status.REFUNDED)
