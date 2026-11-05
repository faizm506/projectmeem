from django.contrib import admin, messages

from core import emails

from .models import SellerPayout, Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "city", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__username", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    actions = ["approve", "suspend"]

    @admin.action(description="Approve selected shops")
    def approve(self, request, queryset):
        count = 0
        for shop in queryset.exclude(status=Shop.Status.APPROVED):
            shop.status = Shop.Status.APPROVED
            shop.save(update_fields=["status"])
            emails.shop_approved(shop)
            count += 1
        self.message_user(request, f"Approved {count} shop(s).", messages.SUCCESS)

    @admin.action(description="Suspend selected shops")
    def suspend(self, request, queryset):
        queryset.update(status=Shop.Status.SUSPENDED)


@admin.register(SellerPayout)
class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ("shop", "amount_minor", "reference", "created_at")
    search_fields = ("shop__name", "reference")
    autocomplete_fields = ("shop",)
