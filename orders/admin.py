from django.contrib import admin, messages

from .models import Dispute, Order, OrderItem
from .services import cancel_pending, refund_order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "shop", "title", "unit_price_minor", "quantity", "line_total_minor",
                       "commission_minor", "seller_earning_minor")
    fields = readonly_fields + ("fulfil_status", "tracking_number")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total_minor", "donation_minor", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("number", "user__username", "user__email", "ship_name")
    inlines = [OrderItemInline]
    actions = ["refund", "cancel_unpaid"]
    readonly_fields = ("number", "user", "subtotal_minor", "shipping_minor", "total_minor", "commission_minor", "donation_minor",
                       "provider", "provider_order_id", "provider_payment_id", "created_at", "paid_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Refund selected paid orders (reverses the donation). Then refund the money in your gateway.")
    def refund(self, request, queryset):
        done = sum(1 for order in queryset if refund_order(order))
        self.message_user(request, f"Refunded {done} order(s). Remember to return the money in the payment gateway dashboard.", messages.SUCCESS)

    @admin.action(description="Cancel selected unpaid orders (returns stock)")
    def cancel_unpaid(self, request, queryset):
        done = sum(1 for order in queryset if cancel_pending(order))
        self.message_user(request, f"Cancelled {done} unpaid order(s).", messages.SUCCESS)


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ("order", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("order__number", "user__username")
    readonly_fields = ("order", "user", "reason", "created_at")
    actions = ["resolve"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected disputes resolved")
    def resolve(self, request, queryset):
        queryset.update(status=Dispute.Status.RESOLVED)
