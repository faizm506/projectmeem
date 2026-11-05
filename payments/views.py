import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order
from orders.services import mark_paid

from .models import PaymentEvent
from .providers import PaymentError, razorpay_create_order, verify_checkout_signature, verify_webhook_signature

log = logging.getLogger(__name__)


@login_required
def start(request, number):
    order = get_object_or_404(Order, number=number, user=request.user)
    if order.status != Order.Status.PENDING:
        return redirect(order)
    provider = settings.PAYMENT_PROVIDER
    if provider == "mock":
        return render(request, "payments/mock.html", {"order": order})
    if provider == "razorpay":
        try:
            if not order.provider_order_id:
                order.provider = "razorpay"
                order.provider_order_id = razorpay_create_order(order)
                order.save(update_fields=["provider", "provider_order_id"])
        except PaymentError:
            messages.error(request, "We could not start the payment. Please try again in a moment.")
            return redirect(order)
        return render(request, "payments/razorpay.html", {"order": order, "key_id": settings.RAZORPAY_KEY_ID})
    raise Http404()


@login_required
@require_POST
def mock_confirm(request, number):
    """TESTING ONLY. Lets you finish a fake payment. Disabled unless PAYMENT_PROVIDER=mock and DEBUG is on."""
    if settings.PAYMENT_PROVIDER != "mock" or not settings.DEBUG:
        raise Http404()
    order = get_object_or_404(Order, number=number, user=request.user)
    mark_paid(order.pk, "mock", f"mock_{order.number}")
    messages.success(request, "Test payment received. Thank you.")
    return redirect(order)


@login_required
@require_POST
def razorpay_verify(request):
    rzp_order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    order = get_object_or_404(Order, provider_order_id=rzp_order_id, user=request.user)
    if verify_checkout_signature(rzp_order_id, payment_id, signature):
        mark_paid(order.pk, "razorpay", payment_id)
        messages.success(request, "Payment received. Thank you.")
    else:
        messages.error(request, "We could not verify that payment. If money left your account, contact us with your order number.")
    return redirect(order)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Razorpay calls this. The signed message, not the browser, is the source of truth for payments."""
    if not verify_webhook_signature(request.body, request.headers.get("X-Razorpay-Signature", "")):
        return HttpResponse(status=400)
    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)
    event = payload.get("event", "")
    if event in ("payment.captured", "order.paid"):
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order = Order.objects.filter(provider_order_id=entity.get("order_id", "")).first()
        if order and entity.get("id") and entity.get("amount") == order.total_minor:
            mark_paid(order.pk, "razorpay", entity["id"])
        else:
            log.warning("Webhook %s did not match an order or amount.", event)
    event_id = request.headers.get("X-Razorpay-Event-Id", "")
    if event_id:
        PaymentEvent.objects.get_or_create(event_id=event_id, defaults={"provider": "razorpay", "event_type": event})
    return HttpResponse("ok")
