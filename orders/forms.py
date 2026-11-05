from django import forms

from accounts.forms import StyledMixin

from .models import Dispute, Order


class ShippingForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ("ship_name", "ship_phone", "ship_line1", "ship_line2", "ship_city", "ship_state", "ship_pincode", "ship_country")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()


class DisputeForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("reason",)
        labels = {"reason": "What went wrong?"}
        widgets = {"reason": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()
