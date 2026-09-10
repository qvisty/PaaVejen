from django.contrib import admin

from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "reviewer", "reviewed_user", "score", "created_at")
    list_filter = ("score",)
