from django.contrib import admin

from .models import Cause, Disbursement, LedgerEntry


@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_charity", "weight", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    """Read only on purpose. The ledger is a permanent record."""

    list_display = ("id", "order", "cause", "entry_type", "amount_minor", "created_at")
    list_filter = ("entry_type", "cause")
    search_fields = ("order__number",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Disbursement)
class DisbursementAdmin(admin.ModelAdmin):
    list_display = ("paid_on", "cause", "charity_name", "amount_minor", "reference")
    list_filter = ("cause",)
