from decimal import ROUND_HALF_UP, Decimal

from django import forms

from accounts.forms import StyledMixin
from catalog.models import Product

from .models import Shop

from core.uploads import sanitize_image

check_image = sanitize_image   # proves it is a real image, shrinks it and re-encodes it


class ShopForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Shop
        fields = ("name", "tagline", "story", "city", "logo", "payout_note")
        widgets = {"story": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()

    def clean_logo(self):
        return check_image(self.cleaned_data.get("logo"))


class ProductForm(StyledMixin, forms.ModelForm):
    price = forms.DecimalField(min_value=Decimal("1"), max_digits=9, decimal_places=2, label="Price (rupees)")

    class Meta:
        model = Product
        fields = ("category", "title", "description", "stock", "image", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["price"].initial = Decimal(self.instance.price_minor) / 100
        self.order_fields(["category", "title", "description", "price", "stock", "image", "is_active"])
        self.style()
        self.fields["is_active"].widget.attrs["class"] = ""

    def clean_image(self):
        return check_image(self.cleaned_data.get("image"))

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.price_minor = int((self.cleaned_data["price"] * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if commit:
            obj.save()
        return obj


class ShipForm(StyledMixin, forms.Form):
    tracking_number = forms.CharField(max_length=80, required=False, label="Tracking number (optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()
