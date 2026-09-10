from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "reporter", "transport_request", "booking", "status", "created_at")
    list_filter = ("status", "source")
    search_fields = ("reason", "reporter__username")
