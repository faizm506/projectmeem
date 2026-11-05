from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from catalog.models import Category, Product
from donations.models import Cause, LedgerEntry
from donations.services import allocate, totals
from orders import services
from orders.models import Order, OrderItem
from shops.models import Shop


class MeemTestCase(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller1", "s@x.test", "pw12345678", role="seller")
        self.shop = Shop.objects.create(owner=self.seller, name="S Shop", slug="s-shop", status="approved")
        self.cat = Category.objects.create(name="Books", slug="books", icon="book", tone="d")
        self.product = Product.objects.create(shop=self.shop, category=self.cat, title="Book", slug="book", price_minor=50000, stock=5)
        self.buyer = User.objects.create_user("buyer1", "b@x.test", "pw12345678")
        Cause.objects.create(name="Gaza", slug="gaza", weight=2)
        Cause.objects.create(name="Yemen", slug="yemen", weight=1)
        self.addr = dict(ship_name="B", ship_phone="9999999999", ship_line1="1 Road", ship_line2="", ship_city="Ahmedabad",
                         ship_state="Gujarat", ship_pincode="380001", ship_country="India")

    def make_order(self, qty=2):
        lines = [{"product": self.product, "qty": qty, "line_total": 50000 * qty}]
        return services.create_order(self.buyer, lines, self.addr)


class DonationMathTests(MeemTestCase):
    def test_allocate_always_sums_to_total(self):
        for total in (1, 2, 99, 101, 2000, 12345):
            self.assertEqual(sum(allocate(total, [2, 1, 1])), total)


class OrderServiceTests(MeemTestCase):
    def test_create_order_snapshots_money_and_reserves_stock(self):
        order = self.make_order(2)
        self.assertEqual(order.subtotal_minor, 100000)
        self.assertEqual(order.shipping_minor, 0)          # at or above the free shipping line
        self.assertEqual(order.commission_minor, 10000)    # 10%
        self.assertEqual(order.donation_minor, 2000)       # 2% of items
        item = order.items.get()
        self.assertEqual(item.seller_earning_minor, 90000)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_small_order_pays_shipping(self):
        order = self.make_order(1)
        self.assertEqual(order.shipping_minor, 4900)
        self.assertEqual(order.total_minor, 54900)

    def test_not_enough_stock(self):
        with self.assertRaises(services.StockError):
            self.make_order(6)

    def test_mark_paid_is_idempotent_and_writes_ledger_once(self):
        order = self.make_order(2)
        self.assertTrue(services.mark_paid(order.pk, "mock", "p1"))
        self.assertFalse(services.mark_paid(order.pk, "mock", "p1"))
        entries = LedgerEntry.objects.filter(order=order)
        self.assertEqual(entries.count(), 2)
        self.assertEqual(sum(e.amount_minor for e in entries), 2000)
        self.assertEqual(totals()["net"], 2000)

    def test_refund_reverses_donation_and_restores_unshipped_stock(self):
        order = self.make_order(2)
        services.mark_paid(order.pk, "mock", "p1")
        self.assertTrue(services.refund_order(order))
        self.assertFalse(services.refund_order(order))
        self.assertEqual(totals()["net"], 0)
        self.assertEqual(LedgerEntry.objects.filter(order=order).count(), 4)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_cancel_pending_restores_stock(self):
        order = self.make_order(2)
        self.assertTrue(services.cancel_pending(order))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_ledger_is_append_only(self):
        order = self.make_order(2)
        services.mark_paid(order.pk, "mock", "p1")
        entry = LedgerEntry.objects.first()
        entry.amount_minor = 1
        with self.assertRaises(RuntimeError):
            entry.save()
        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.all().delete()
        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.all().update(amount_minor=0)

    def test_seller_balance_moves_on_delivery(self):
        order = self.make_order(2)
        services.mark_paid(order.pk, "mock", "p1")
        self.assertEqual(self.shop.balance(), {"pending": 90000, "available": 0, "paid_out": 0})
        OrderItem.objects.filter(order=order).update(fulfil_status=OrderItem.Fulfil.DELIVERED)
        self.assertEqual(self.shop.balance()["available"], 90000)

    def test_emails_sent_after_payment(self):
        order = self.make_order(2)
        with self.captureOnCommitCallbacks(execute=True):
            services.mark_paid(order.pk, "mock", "p1")
        subjects = " ".join(m.subject for m in mail.outbox)
        self.assertIn("confirmed", subjects)
        self.assertIn("donation", subjects)
        self.assertIn("New order", subjects)


@override_settings(DEBUG=True, PAYMENT_PROVIDER="mock")
class FlowTests(MeemTestCase):
    def test_public_pages_load(self):
        for name in ("core:home", "catalog:list", "shops:list", "donations:impact", "core:terms",
                     "core:privacy", "core:refunds", "core:seller_agreement", "accounts:login", "accounts:signup"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(self.shop.get_absolute_url()).status_code, 200)

    def test_full_buyer_journey(self):
        c = self.client
        c.force_login(self.buyer)
        c.post(reverse("cart:add", args=[self.product.pk]), {"qty": 2})
        self.assertEqual(c.get(reverse("cart:detail")).status_code, 200)
        response = c.post(reverse("orders:checkout"), self.addr)
        order = Order.objects.get(user=self.buyer)
        self.assertRedirects(response, reverse("payments:start", args=[order.number]))
        self.assertEqual(c.get(reverse("payments:start", args=[order.number])).status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            c.post(reverse("payments:mock_confirm", args=[order.number]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertContains(c.get(reverse("donations:impact")), "₹20")
        self.assertContains(c.get(order.get_absolute_url()), order.number)

    def test_seller_pages_need_login_and_shop(self):
        self.assertEqual(self.client.get(reverse("shops:dashboard")).status_code, 302)
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("shops:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("shops:orders")).status_code, 200)

    def test_buyer_cannot_open_someone_elses_order(self):
        order = self.make_order(1)
        other = User.objects.create_user("other", "o@x.test", "pw12345678")
        self.client.force_login(other)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
