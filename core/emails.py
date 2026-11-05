"""All MEEM emails in one place. Plain text, short and warm. Console backend prints them in dev."""
from django.conf import settings
from django.core.mail import send_mail

from .templatetags.meem import money


def _send(subject, body, to):
    if not to:
        return
    send_mail(f"[MEEM] {subject}", body, settings.DEFAULT_FROM_EMAIL, [to] if isinstance(to, str) else list(to), fail_silently=True)


def welcome(user):
    _send("Welcome to MEEM", f"Assalamu alaikum {user.username},\n\nWelcome to MEEM, one trusted space for Muslim-owned brands.\n"
          "Every order you place sets aside a small donation for Muslims in need.\n\nMade with purpose.\nThe MEEM team", user.email)


def order_confirmed(order):
    lines = "\n".join(f"- {i.title} x {i.quantity}: {money(i.line_total_minor)}" for i in order.items.all())
    body = (f"Thank you for your order {order.number}.\n\n{lines}\n\nItems: {money(order.subtotal_minor)}\n"
            f"Shipping: {money(order.shipping_minor)}\nTotal: {money(order.total_minor)}\n\n"
            f"A donation of {money(order.donation_minor)} has been set aside from this order. "
            "You can see where donations go on the Impact page.\n\nWe will email you when each item ships.")
    _send(f"Order {order.number} confirmed", body, order.user.email)


def new_order_for_seller(order, shop, items):
    lines = "\n".join(f"- {i.title} x {i.quantity} ({money(i.line_total_minor)})" for i in items)
    body = (f"You have a new paid order {order.number}.\n\n{lines}\n\nShip to:\n{order.ship_name}, {order.ship_line1} {order.ship_line2}\n"
            f"{order.ship_city}, {order.ship_state} {order.ship_pincode}\nPhone: {order.ship_phone}\n\n"
            "Open your seller dashboard to add a tracking number once you ship.")
    _send(f"New order {order.number}", body, shop.owner.email)


def item_shipped(item):
    order = item.order
    body = (f"Good news. {item.title} from {item.shop.name} is on its way.\nOrder: {order.number}\n"
            f"Tracking: {item.tracking_number or 'not provided'}\n\nJazakAllah khair for shopping with MEEM.")
    _send(f"Your item shipped ({order.number})", body, order.user.email)


def donation_recorded(order):
    body = (f"Your order {order.number} set aside {money(order.donation_minor)} for Muslims in need.\n"
            "Thank you for shopping with purpose. See the totals any time on the Impact page.")
    _send("Your donation has been recorded", body, order.user.email)


def order_refunded(order):
    _send(f"Order {order.number} refunded", f"Your order {order.number} has been marked as refunded.\n"
          "The money returns to your original payment method. This can take a few days.", order.user.email)


def shop_approved(shop):
    _send("Your MEEM shop is approved", f"Congratulations. {shop.name} is approved and live on MEEM.\n"
          "Sign in and add your products from the seller dashboard.", shop.owner.email)


def shop_submitted(shop):
    _send("New shop waiting for approval", f"{shop.name} (owner: {shop.owner.username}) is waiting for approval in the admin.", settings.ADMIN_NOTIFY_EMAIL)


def dispute_opened(dispute):
    _send(f"Dispute on order {dispute.order.number}", f"{dispute.user.username} reported a problem:\n\n{dispute.reason}", settings.ADMIN_NOTIFY_EMAIL)
