from django.contrib import admin

from .models import SiteSetting, WaitlistEntry


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ("email", "interest", "created_at")
    list_filter = ("interest",)
    search_fields = ("email",)
