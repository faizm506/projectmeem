from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product
from core.models import SiteSetting

from .cart import Cart


def _int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def detail(request):
    cart = Cart(request)
    lines = cart.lines()
    subtotal = cart.subtotal(lines)
    setting = SiteSetting.get()
    shipping = 0 if (not lines or subtotal >= setting.free_shipping_over_minor) else setting.shipping_flat_minor
    donation = (subtotal * setting.donation_bps) // 10000
    return render(request, "cart/cart.html", {
        "lines": lines, "subtotal": subtotal, "shipping": shipping, "total": subtotal + shipping, "donation": donation,
        "free_over": setting.free_shipping_over_minor,
    })


@require_POST
def add(request, pk):
    product = get_object_or_404(Product.objects.visible(), pk=pk)
    qty = max(1, _int(request.POST.get("qty"), 1))
    if not product.in_stock:
        messages.error(request, "Sorry, this item is out of stock.")
    else:
        Cart(request).add(product.pk, qty)
        messages.success(request, f"Added {product.title} to your cart.")
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect("cart:detail")


@require_POST
def update(request, pk):
    Cart(request).set(pk, _int(request.POST.get("qty"), 1))
    return redirect("cart:detail")


@require_POST
def remove(request, pk):
    Cart(request).remove(pk)
    return redirect("cart:detail")
