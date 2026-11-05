"""Order logic. Money is whole paise. Every state change is idempotent so repeated webhooks are harmless."""
import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Product
from core import emails
from core.models import SiteSetting
from donations.services import record_donation, reverse_donation

from .models import Order, OrderItem

log = logging.getLogger(__name__)


class StockError(Exception):
    pass


@transaction.atomic
def create_order(user, lines, address):
    """Create a pending order from cart lines and reserve stock. `address` is a dict of ship_* values."""
    setting = SiteSetting.get()
    order = Order(user=user, **address)
    items, subtotal, commission = [], 0, 0
    for line in lines:
        product = Product.objects.select_related("shop").get(pk=line["product"].pk)
        qty = line["qty"]
        if not product.is_active or not product.shop.is_approved or product.stock < qty:
            raise StockError(f"Sorry, {product.title} is no longer available in that quantity.")
        line_total = product.price_minor * qty
        item_commission = (line_total * setting.commission_bps) // 10000
        items.append(OrderItem(
            product=product, shop=product.shop, title=product.title, unit_price_minor=product.price_minor, quantity=qty,
            line_total_minor=line_total, commission_minor=item_commission, seller_earning_minor=line_total - item_commission))
        subtotal += line_total
        commission += item_commission
    if not items:
        raise StockError("Your cart is empty.")
    shipping = 0 if subtotal >= setting.free_shipping_over_minor else setting.shipping_flat_minor
    order.subtotal_minor = subtotal
    order.shipping_minor = shipping
    order.total_minor = subtotal + shipping
    order.commission_minor = commission
    order.donation_minor = min((subtotal * setting.donation_bps) // 10000, commission)
    order.save()
    for item in items:
        item.order = order
        item.save()
        updated = Product.objects.filter(pk=item.product_id, stock__gte=item.quantity).update(stock=F("stock") - item.quantity)
        if updated != 1:
            raise StockError(f"Sorry, {item.title} just sold out.")
    return order


def _after_paid(order_id):
    order = Order.objects.select_related("user").get(pk=order_id)
    emails.order_confirmed(order)
    emails.donation_recorded(order)
    by_shop = {}
    for item in order.items.select_related("shop__owner"):
        by_shop.setdefault(item.shop, []).append(item)
    for shop, items in by_shop.items():
        emails.new_order_for_seller(order, shop, items)


@transaction.atomic
def mark_paid(order_id, provider, payment_id):
    """Mark an order paid and record its donation. Returns True only the first time."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status == Order.Status.PAID:
        return False
    if order.status != Order.Status.PENDING:
        log.warning("Payment %s arrived for %s order %s. Needs a manual look.", payment_id, order.status, order.number)
        return False
    order.status = Order.Status.PAID
    order.provider = provider
    order.provider_payment_id = payment_id
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "provider", "provider_payment_id", "paid_at"])
    record_donation(order)
    transaction.on_commit(lambda: _after_paid(order.pk))
    return True


def _restore_stock(items):
    for item in items:
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)


@transaction.atomic
def cancel_pending(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        return False
    _restore_stock(order.items.all())
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    return True


@transaction.atomic
def refund_order(order):
    """Mark a paid order refunded, reverse its donation and return unshipped items to stock.
    The actual money goes back from your payment gateway dashboard (Version 1 is manual)."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PAID:
        return False
    order.status = Order.Status.REFUNDED
    order.save(update_fields=["status"])
    reverse_donation(order)
    _restore_stock(order.items.filter(fulfil_status=OrderItem.Fulfil.PLACED))
    transaction.on_commit(lambda: emails.order_refunded(Order.objects.select_related("user").get(pk=order.pk)))
    return True
