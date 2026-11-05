from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Category, Product
from donations.models import Cause
from donations.services import totals

from .models import WaitlistEntry
from .security import throttle


def home(request):
    products = Product.objects.visible().select_related("shop", "category").order_by("-created_at")[:8]
    return render(request, "core/home.html", {
        "categories": Category.objects.all(),
        "products": products,
        "causes": Cause.objects.filter(is_active=True),
        "impact": totals(),
    })


class WaitlistForm(forms.Form):
    email = forms.EmailField()
    interest = forms.ChoiceField(choices=WaitlistEntry.Interest.choices, required=False)


@require_POST
@throttle("waitlist", 20, 3600)
def waitlist(request):
    if request.POST.get("website"):          # honeypot
        return redirect("/#join")
    form = WaitlistForm(request.POST)
    if form.is_valid():
        _, created = WaitlistEntry.objects.get_or_create(
            email=form.cleaned_data["email"].lower(),
            defaults={"interest": form.cleaned_data.get("interest") or "buyer"})
        messages.success(request, "You are on the list. We will be in touch soon." if created else "You are already on the list. Thank you.")
    else:
        messages.error(request, "Please enter a valid email address.")
    return redirect("/#join")


def policy(template):
    def view(request):
        return render(request, template)
    return view
