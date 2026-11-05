from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.cart import Cart
from core import emails
from core.models import SiteSetting
from core.security import throttle

from .forms import DisputeForm, ShippingForm
from .models import Order
from .services import StockError, create_order


@login_required
@throttle("checkout", 30, 3600)
def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:detail")
    last = Order.objects.filter(user=request.user).first()
    initial = {}
    if last:
        initial = {f: getattr(last, f) for f in ShippingForm.Meta.fields}
    elif request.user.get_full_name():
        initial = {"ship_name": request.user.get_full_name(), "ship_phone": request.user.phone}
    form = ShippingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            order = create_order(request.user, lines, form.cleaned_data)
        except StockError as err:
            messages.error(request, str(err))
            return redirect("cart:detail")
        cart.clear()
        return redirect("payments:start", number=order.number)
    setting = SiteSetting.get()
    subtotal = cart.subtotal(lines)
    shipping = 0 if subtotal >= setting.free_shipping_over_minor else setting.shipping_flat_minor
    return render(request, "orders/checkout.html", {
        "form": form, "lines": lines, "subtotal": subtotal, "shipping": shipping, "total": subtotal + shipping,
        "donation": (subtotal * setting.donation_bps) // 10000,
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders/list.html", {"orders": orders})


@login_required
def order_detail(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items__shop", "disputes"), number=number, user=request.user)
    return render(request, "orders/detail.html", {"order": order, "dispute_form": DisputeForm()})


@login_required
@require_POST
@throttle("dispute", 10, 3600)
def dispute_create(request, number):
    order = get_object_or_404(Order, number=number, user=request.user)
    form = DisputeForm(request.POST)
    if order.status == Order.Status.PAID and form.is_valid():
        dispute = form.save(commit=False)
        dispute.order = order
        dispute.user = request.user
        dispute.save()
        emails.dispute_opened(dispute)
        messages.success(request, "Thank you. We received your report and will look into it.")
    else:
        messages.error(request, "We could not send that report. Please try again.")
    return redirect(order)
