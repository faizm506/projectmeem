from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MeemUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("MEEM", {"fields": ("role", "phone")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("MEEM", {"fields": ("email", "role", "phone")}),)
