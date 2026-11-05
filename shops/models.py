from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse


class Shop(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for approval"
        APPROVED = "approved", "Approved"
        SUSPENDED = "suspended", "Suspended"

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop")
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    tagline = models.CharField(max_length=140, blank=True)
    story = models.TextField(blank=True, help_text="Tell buyers who you are and what you make.")
    city = models.CharField(max_length=80, blank=True)
    logo = models.ImageField(upload_to="shops/", blank=True)
    payout_note = models.CharField(
        max_length=200, blank=True,
        help_text="Your UPI ID. Do not type bank account numbers here; send them privately to the MEEM team.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shops:detail", args=[self.slug])

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    def balance(self):
        """Seller money in paise: pending (paid, not delivered), available (delivered, not paid out), paid out."""
        from orders.models import Order, OrderItem

        items = OrderItem.objects.filter(shop=self, order__status=Order.Status.PAID)
        delivered = items.filter(fulfil_status=OrderItem.Fulfil.DELIVERED).aggregate(t=Sum("seller_earning_minor"))["t"] or 0
        pending = items.exclude(fulfil_status=OrderItem.Fulfil.DELIVERED).aggregate(t=Sum("seller_earning_minor"))["t"] or 0
        paid_out = self.payouts.aggregate(t=Sum("amount_minor"))["t"] or 0
        return {"pending": pending, "available": delivered - paid_out, "paid_out": paid_out}


class SellerPayout(models.Model):
    """Recorded by an admin after sending money to the seller (manual in Version 1)."""

    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="payouts")
    amount_minor = models.PositiveIntegerField(help_text="In paise (100 paise = 1 rupee).")
    reference = models.CharField(max_length=120, help_text="UPI or bank transfer reference.")
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shop} payout {self.amount_minor}"
