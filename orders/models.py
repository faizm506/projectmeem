import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_number():
    return "MEEM-" + "".join(secrets.choice(ALPHABET) for _ in range(8))


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for payment"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)

    subtotal_minor = models.PositiveIntegerField(default=0)
    shipping_minor = models.PositiveIntegerField(default=0)
    total_minor = models.PositiveIntegerField(default=0)
    commission_minor = models.PositiveIntegerField(default=0, help_text="MEEM's commission on this order.")
    donation_minor = models.PositiveIntegerField(default=0, help_text="Donation set aside (paid from the commission).")

    ship_name = models.CharField("Full name", max_length=100)
    ship_phone = models.CharField("Phone", max_length=20)
    ship_line1 = models.CharField("Address line 1", max_length=150)
    ship_line2 = models.CharField("Address line 2", max_length=150, blank=True)
    ship_city = models.CharField("City", max_length=80)
    ship_state = models.CharField("State", max_length=80)
    ship_pincode = models.CharField("PIN code", max_length=12)
    ship_country = models.CharField("Country", max_length=60, default="India")

    provider = models.CharField(max_length=20, blank=True)
    provider_order_id = models.CharField(max_length=80, blank=True, db_index=True)
    provider_payment_id = models.CharField(max_length=80, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            number = new_number()
            while Order.objects.filter(number=number).exists():
                number = new_number()
            self.number = number
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.number])


class OrderItem(models.Model):
    class Fulfil(models.TextChoices):
        PLACED = "placed", "Placed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    shop = models.ForeignKey("shops.Shop", on_delete=models.PROTECT, related_name="order_items")
    title = models.CharField(max_length=120)
    unit_price_minor = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    line_total_minor = models.PositiveIntegerField()
    commission_minor = models.PositiveIntegerField(default=0)
    seller_earning_minor = models.PositiveIntegerField(default=0)
    fulfil_status = models.CharField(max_length=10, choices=Fulfil.choices, default=Fulfil.PLACED)
    tracking_number = models.CharField(max_length=80, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} x {self.quantity}"


class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="disputes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispute on {self.order.number}"
