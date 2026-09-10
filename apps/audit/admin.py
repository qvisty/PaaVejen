from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "event_type", "user", "booking", "metadata")
    list_filter = ("event_type",)
    search_fields = ("event_type", "user__username")
    readonly_fields = ("user", "booking", "event_type", "metadata", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
