from django import template
from django.conf import settings

register = template.Library()


@register.filter
def money(minor):
    """Format paise as rupees: 129900 -> ₹1,299 and 129950 -> ₹1,299.50"""
    try:
        minor = int(minor)
    except (TypeError, ValueError):
        return ""
    neg = minor < 0
    rupees, paise = divmod(abs(minor), 100)
    text = f"{rupees:,}"
    if paise:
        text += f".{paise:02d}"
    return f"{'-' if neg else ''}{settings.CURRENCY_SYMBOL}{text}"


@register.filter
def percent_bps(bps):
    try:
        value = int(bps) / 100
    except (TypeError, ValueError):
        return ""
    return f"{value:g}%"
