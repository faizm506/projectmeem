from django.core.exceptions import ValidationError
from django.db import models


class SiteSetting(models.Model):
    """One row of marketplace settings, editable in the admin. Money is in paise (1/100 rupee)."""

    donation_bps = models.PositiveIntegerField(
        default=200, help_text="Donation as basis points of the items subtotal. 200 = 2%. Paid out of MEEM's commission.")
    commission_bps = models.PositiveIntegerField(
        default=1000, help_text="MEEM commission as basis points of each item. 1000 = 10%.")
    shipping_flat_minor = models.PositiveIntegerField(default=4900, help_text="Flat shipping per order, in paise (4900 = 49).")
    free_shipping_over_minor = models.PositiveIntegerField(
        default=99900, help_text="Orders at or above this subtotal ship free, in paise (99900 = 999).")
    contact_email = models.EmailField(default="hello@meem.example")

    class Meta:
        verbose_name = "marketplace settings"
        verbose_name_plural = "marketplace settings"

    def __str__(self):
        return "Marketplace settings"

    def clean(self):
        if self.donation_bps > self.commission_bps:
            raise ValidationError("The donation share cannot be bigger than MEEM's commission, because it is paid from it.")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WaitlistEntry(models.Model):
    class Interest(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"

    email = models.EmailField(unique=True)
    interest = models.CharField(max_length=10, choices=Interest.choices, default=Interest.BUYER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "waitlist entries"

    def __str__(self):
        return self.email
