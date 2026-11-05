from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from .models import Cause, Disbursement, LedgerEntry


def allocate(total, weights):
    """Split `total` paise by weights using whole numbers. Leftover paise go to the first causes. Always sums to total."""
    weight_sum = sum(weights)
    shares = [total * w // weight_sum for w in weights]
    leftover = total - sum(shares)
    i = 0
    while leftover > 0:
        shares[i % len(shares)] += 1
        leftover -= 1
        i += 1
    return shares


@transaction.atomic
def record_donation(order):
    """Create ledger rows for a paid order. Safe to call twice: the unique constraint and the check stop duplicates."""
    if order.donation_minor <= 0:
        return []
    if LedgerEntry.objects.filter(order=order, entry_type=LedgerEntry.Type.ACCRUED).exists():
        return []
    causes = list(Cause.objects.filter(is_active=True).order_by("id"))
    if not causes:
        causes = [Cause.objects.get_or_create(slug="general", defaults={"name": "General fund", "description": "Wherever help is needed most."})[0]]
    shares = allocate(order.donation_minor, [c.weight or 1 for c in causes])
    created = []
    for cause, amount in zip(causes, shares):
        if amount > 0:
            created.append(LedgerEntry.objects.create(order=order, cause=cause, amount_minor=amount, entry_type=LedgerEntry.Type.ACCRUED))
    return created


@transaction.atomic
def reverse_donation(order):
    """On refund, add negative rows that cancel the accrued ones. The originals stay untouched."""
    for entry in LedgerEntry.objects.filter(order=order, entry_type=LedgerEntry.Type.ACCRUED):
        LedgerEntry.objects.get_or_create(
            order=order, cause=entry.cause, entry_type=LedgerEntry.Type.REVERSAL,
            defaults={"amount_minor": -entry.amount_minor})


def totals():
    """Numbers for the public Impact page (all in paise)."""
    from orders.models import Order

    net = LedgerEntry.objects.aggregate(t=Sum("amount_minor"))["t"] or 0
    sent = Disbursement.objects.aggregate(t=Sum("amount_minor"))["t"] or 0
    causes = []
    for cause in Cause.objects.all():
        cause_net = cause.ledger_entries.aggregate(t=Sum("amount_minor"))["t"] or 0
        cause_sent = cause.disbursements.aggregate(t=Sum("amount_minor"))["t"] or 0
        if cause.is_active or cause_net or cause_sent:
            causes.append({"cause": cause, "net": cause_net, "sent": cause_sent, "waiting": cause_net - cause_sent})
    return {
        "net": net, "sent": sent, "waiting": net - sent, "causes": causes,
        "orders": Order.objects.filter(status=Order.Status.PAID).count(),
    }


def monthly():
    rows = (LedgerEntry.objects.annotate(month=TruncMonth("created_at")).values("month")
            .annotate(total=Sum("amount_minor")).order_by("-month")[:12])
    return list(rows)
