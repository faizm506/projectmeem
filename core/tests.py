from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from core.uploads import sanitize_image
from orders.models import OrderItem
from orders.tests import MeemTestCase
from orders import services
from shops.models import Shop
from catalog.models import Product


def png_bytes(size=(40, 30), color=(36, 90, 72)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


class SecurityHeaderTests(TestCase):
    def test_headers_are_set(self):
        r = self.client.get(reverse("core:home"))
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
        self.assertIn("object-src 'none'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("Permissions-Policy", r.headers)

    def test_no_inline_scripts_on_home(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn("onclick=", html)
        # every <script> must load a file (strict CSP forbids inline script)
        import re
        for tag in re.findall(r"<script\b[^>]*>", html):
            self.assertIn("src=", tag)


class LoginSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("amina", "a@x.test", "a-long-pass-123")

    def test_normal_login_works(self):
        r = self.client.post(reverse("accounts:login"), {"username": "amina", "password": "a-long-pass-123"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_lockout_after_five_failures_even_with_right_password(self):
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"username": "amina", "password": "wrong"})
        r = self.client.post(reverse("accounts:login"), {"username": "amina", "password": "a-long-pass-123"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Too many sign-in attempts")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_needs_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_private_pages_redirect_to_login(self):
        for name in ("orders:list", "orders:checkout", "shops:dashboard"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn("/accounts/login/", r["Location"])

    def test_signed_in_pages_are_not_cached(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("orders:list"))
        self.assertIn("no-store", r.headers["Cache-Control"])


class BotProtectionTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_signup_honeypot_creates_nothing(self):
        self.client.post(reverse("accounts:signup"), {"username": "bot", "email": "b@x.test", "password1": "x", "password2": "x", "role": "buyer", "website": "spam"})
        self.assertFalse(User.objects.filter(username="bot").exists())

    def test_waitlist_honeypot(self):
        from core.models import WaitlistEntry
        self.client.post(reverse("core:waitlist"), {"email": "bot@x.test", "website": "spam"})
        self.assertFalse(WaitlistEntry.objects.exists())

    def test_signup_is_rate_limited(self):
        for _ in range(10):
            self.client.post(reverse("accounts:signup"), {"website": "spam"})
        self.assertEqual(self.client.post(reverse("accounts:signup"), {"website": "spam"}).status_code, 429)


class UploadSafetyTests(TestCase):
    def test_rejects_text_pretending_to_be_image(self):
        fake = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")
        with self.assertRaises(ValidationError):
            sanitize_image(fake)

    def test_accepts_and_reencodes_real_image(self):
        ok = SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")
        clean = sanitize_image(ok)
        self.assertTrue(clean.name.endswith(".png"))
        self.assertNotIn("photo", clean.name)               # name is random, never the user's file name
        Image.open(BytesIO(clean.read())).verify()

    def test_rejects_huge_files(self):
        big = SimpleUploadedFile("big.png", png_bytes() + b"0" * (3 * 1024 * 1024), content_type="image/png")
        with self.assertRaises(ValidationError):
            sanitize_image(big)


class PaymentSecurityTests(MeemTestCase):
    def test_webhook_rejects_bad_signature(self):
        with override_settings(RAZORPAY_WEBHOOK_SECRET="s3cret"):
            r = self.client.post(reverse("payments:razorpay_webhook"), data=b"{}", content_type="application/json", headers={"X-Razorpay-Signature": "bad"})
        self.assertEqual(r.status_code, 400)

    def test_webhook_closed_when_no_secret_is_set(self):
        with override_settings(RAZORPAY_WEBHOOK_SECRET=""):
            r = self.client.post(reverse("payments:razorpay_webhook"), data=b"{}", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    @override_settings(DEBUG=False, PAYMENT_PROVIDER="mock")
    def test_fake_payment_is_impossible_outside_debug(self):
        order = self.make_order(1)
        self.client.force_login(self.buyer)
        r = self.client.post(reverse("payments:mock_confirm", args=[order.number]))
        self.assertEqual(r.status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.status, "pending")


class AccessControlTests(MeemTestCase):
    def test_other_seller_cannot_ship_my_item(self):
        order = self.make_order(1)
        services.mark_paid(order.pk, "mock", "p1")
        item = OrderItem.objects.get(order=order)
        rival = User.objects.create_user("rival", "r@x.test", "a-long-pass-123", role="seller")
        Shop.objects.create(owner=rival, name="Rival", slug="rival", status="approved")
        self.client.force_login(rival)
        r = self.client.post(reverse("shops:item_ship", args=[item.pk]), {"tracking_number": "X"})
        self.assertEqual(r.status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.fulfil_status, "placed")

    def test_other_seller_cannot_edit_my_product(self):
        rival = User.objects.create_user("rival", "r@x.test", "a-long-pass-123", role="seller")
        Shop.objects.create(owner=rival, name="Rival", slug="rival", status="approved")
        self.client.force_login(rival)
        self.assertEqual(self.client.get(reverse("shops:product_edit", args=[self.product.pk])).status_code, 404)

    def test_buyer_without_shop_cannot_open_dashboard(self):
        self.client.force_login(self.buyer)
        r = self.client.get(reverse("shops:dashboard"))
        self.assertEqual(r.status_code, 302)

    def test_cart_quantity_cannot_be_negative_or_huge(self):
        self.client.post(reverse("cart:add", args=[self.product.pk]), {"qty": "-5"})
        self.client.post(reverse("cart:add", args=[self.product.pk]), {"qty": "9999"})
        from cart.cart import Cart
        from django.test import RequestFactory
        r = self.client.get(reverse("cart:detail"))
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(self.client.session.get("cart", {})) and sum(self.client.session["cart"].values()), 10)

    def test_prices_come_from_the_server_not_the_browser(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("cart:add", args=[self.product.pk]), {"qty": "1", "price": "1"})
        self.client.post(reverse("orders:checkout"), self.addr)
        from orders.models import Order
        self.assertEqual(Order.objects.get(user=self.buyer).subtotal_minor, 50000)


class SeedBulkTests(TestCase):
    @override_settings(DEBUG=True)
    def test_bulk_seed_builds_a_consistent_marketplace(self):
        from django.core.management import call_command
        from django.db.models import Sum
        from donations.models import LedgerEntry
        from orders.models import Order
        call_command("seed_bulk", sellers=8, shoppers=6, orders=25, verbosity=0)
        self.assertGreaterEqual(Shop.objects.filter(owner__username__startswith="seller_0").count(), 8)
        self.assertGreater(Product.objects.count(), 20)
        paid = Order.objects.filter(status="paid")
        self.assertTrue(paid.exists())
        # the ledger must always equal the donations of paid orders (refunds are cancelled by reversal rows)
        ledger = LedgerEntry.objects.aggregate(t=Sum("amount_minor"))["t"] or 0
        expected = paid.aggregate(t=Sum("donation_minor"))["t"] or 0
        self.assertEqual(ledger, expected)
        # no product may ever go below zero stock
        self.assertFalse(Product.objects.filter(stock__lt=0).exists())
