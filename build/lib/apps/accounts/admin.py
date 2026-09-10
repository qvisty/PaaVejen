from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PaaVejenUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PåVejen", {"fields": ("phone",)}),)
    list_display = ("username", "email", "first_name", "last_name", "phone", "is_staff")
