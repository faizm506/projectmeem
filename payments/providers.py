"""Payment helpers. The mock provider needs nothing. Razorpay uses only the standard library (no SDK)."""
import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request

from django.conf import settings


class PaymentError(Exception):
    pass


def razorpay_create_order(order):
    """Create a Razorpay order for this MEEM order and return its id."""
    if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        raise PaymentError("Razorpay keys are not set.")
    body = json.dumps({"amount": order.total_minor, "currency": settings.CURRENCY_CODE, "receipt": order.number}).encode()
    token = base64.b64encode(f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()).decode()
    req = urllib.request.Request("https://api.razorpay.com/v1/orders", data=body, method="POST",
                                 headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)["id"]
    except (urllib.error.URLError, ValueError, KeyError) as err:
        raise PaymentError("Could not reach the payment gateway.") from err


def _hmac(secret, message):
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_checkout_signature(rzp_order_id, payment_id, signature):
    expected = _hmac(settings.RAZORPAY_KEY_SECRET, f"{rzp_order_id}|{payment_id}".encode())
    return hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(raw_body, signature):
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    return hmac.compare_digest(_hmac(settings.RAZORPAY_WEBHOOK_SECRET, raw_body), signature or "")
