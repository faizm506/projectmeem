from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order
from orders.services import cancel_pending


class Command(BaseCommand):
    help = "Cancel unpaid orders older than N minutes and give their stock back. Run this from cron every 15 minutes."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=60)

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(minutes=opts["minutes"])
        count = 0
        for order in Order.objects.filter(status=Order.Status.PENDING, created_at__lt=cutoff):
            if cancel_pending(order):
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Cancelled {count} unpaid order(s)."))
