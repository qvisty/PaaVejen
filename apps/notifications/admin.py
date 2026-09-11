from django.contrib import admin

from .models import PushConfig, PushSubscription


@admin.register(PushConfig)
class PushConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "public_key", "created_at")
    readonly_fields = ("private_key_pem", "public_key", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "endpoint", "created_at")
    search_fields = ("user__username", "endpoint")
