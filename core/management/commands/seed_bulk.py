"""Fill a development database with a realistic marketplace: ~50 sellers, ~50 shoppers, products, 60 days of orders,
donations, payouts, charity transfers and a few disputes. Development only. Safe to run again (adds more orders)."""
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet, Sum
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from catalog.models import Category, Product
from core.models import WaitlistEntry
from donations.models import Cause, Disbursement, LedgerEntry
from orders import services
from orders.models import Dispute, Order, OrderItem
from shops.models import SellerPayout, Shop

PREFIX = ["Noor", "Barakah", "Iqra", "Hilal", "Safa", "Marwa", "Zamzam", "Amanah", "Rahma", "Falah",
          "Sabr", "Nur", "Ihsan", "Huda", "Salam", "Yaqeen", "Taqwa", "Jannah", "Qalam", "Ummah"]
SUFFIX = {"Modest fashion": "Modest Wear", "Halal skincare": "Botanicals", "Islamic books": "Books",
          "Tech": "Tech Co", "Home": "Home & Decor", "Gifts": "Gift House"}
CITIES = [("Ahmedabad", "Gujarat", "380001"), ("Hyderabad", "Telangana", "500001"), ("Mumbai", "Maharashtra", "400001"),
          ("Delhi", "Delhi", "110001"), ("Bengaluru", "Karnataka", "560001"), ("Kolkata", "West Bengal", "700001"),
          ("Lucknow", "Uttar Pradesh", "226001"), ("Chennai", "Tamil Nadu", "600001"), ("Jaipur", "Rajasthan", "302001"),
          ("Bhopal", "Madhya Pradesh", "462001"), ("Surat", "Gujarat", "395003"), ("Kochi", "Kerala", "682001")]
FIRST = ["Amina", "Yusuf", "Maryam", "Ibrahim", "Layla", "Omar", "Zainab", "Hamza", "Fatima", "Bilal", "Sara", "Idris",
         "Khadija", "Zayd", "Aisha", "Hassan", "Safiya", "Ismail", "Hana", "Salman", "Rukhsar", "Imran", "Nadia", "Farhan"]
LAST = ["Khan", "Sheikh", "Ansari", "Qureshi", "Siddiqui", "Patel", "Memon", "Shaikh", "Pathan", "Mirza", "Syed", "Chaudhary"]
COLORS = ["Sage", "Sand", "Olive", "Charcoal", "Cream", "Midnight", "Rose", "Walnut"]
# (title, min rupees, max rupees)
CATALOG = {
    "Modest fashion": [("Linen {c} Abaya", 1899, 3499), ("{c} Cotton Hijab Set", 599, 999), ("{c} Embroidered Kaftan", 2499, 4499),
                       ("{c} Modal Jersey Hijab", 299, 549), ("Prayer Dress with Hijab, {c}", 1299, 1999), ("Men's Cotton Thobe, {c}", 1499, 2499),
                       ("Kids Eid Thobe, {c}", 899, 1499), ("{c} Pleated Maxi Skirt", 999, 1799)],
    "Halal skincare": [("Rose Water Toner", 249, 449), ("Black Seed Face Oil", 449, 799), ("Argan Hand Cream", 199, 399),
                       ("Vitamin C Serum (alcohol-free)", 549, 999), ("Shea Body Butter", 349, 649), ("Charcoal Soap Bar", 129, 249),
                       ("Lip Balm Trio", 199, 349), ("Henna Hair Mask", 299, 549)],
    "Islamic books": [("Stories of the Prophets (Kids)", 499, 899), ("Daily Duas Pocket Edition", 149, 349), ("Seerah in Short", 349, 649),
                      ("Names of Allah Journal", 299, 549), ("Ramadan Planner", 249, 449), ("Quran Tafsir Starter", 699, 1299),
                      ("Arabic Alphabet Flashcards", 199, 399), ("Hadith for Teens", 399, 749)],
    "Tech": [("Prayer Times Smart Clock", 1499, 2999), ("Qibla Compass Keychain", 149, 299), ("Wireless Charging Pad", 799, 1499),
             ("Quran Reader Pen", 2499, 4499), ("Bluetooth Speaker (Adhan)", 1299, 2499), ("Phone Stand, Walnut", 349, 699),
             ("Travel Adapter Kit", 599, 1099), ("Digital Tasbih Ring", 399, 799)],
    "Home": [("Plush Prayer Mat, {c}", 699, 1299), ("Ceramic Date Bowl", 399, 799), ("Oud Wood Incense Set", 499, 999),
             ("Calligraphy Wall Art", 899, 1999), ("Quran Stand, Walnut", 599, 1199), ("Linen Table Runner, {c}", 449, 849),
             ("Brass Coffee Dallah", 1299, 2499), ("Amber Scented Candle", 349, 649)],
    "Gifts": [("Eid Gift Box", 999, 1999), ("Ramadan Dates Hamper", 799, 1599), ("Wedding Mubarak Card Set", 199, 399),
              ("Personalised Name Plaque", 599, 1199), ("Zamzam Gift Set", 699, 1299), ("Kids Eid Activity Kit", 399, 799),
              ("Miswak Travel Pack", 149, 299), ("Gold-Tone Tasbih", 449, 899)],
}
BLURB = ["Made in small batches by a Muslim-owned family business.", "Carefully made and checked before it ships.",
         "A customer favourite, loved for its quality and honest price.", "Simple, beautiful and made to last.",
         "Packed with care and shipped within two days."]
REASONS = ["The parcel arrived late and the box was damaged.", "The colour is different from the photo.", "I was charged but the item is missing."]


class Command(BaseCommand):
    help = "Create ~50 sellers, ~50 shoppers, products and a realistic order history. Development only."

    def add_arguments(self, parser):
        parser.add_argument("--sellers", type=int, default=50)
        parser.add_argument("--shoppers", type=int, default=50)
        parser.add_argument("--orders", type=int, default=220)
        parser.add_argument("--seed", type=int, default=2026)

    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError("seed_bulk creates accounts with a known password. It only runs with DEBUG=1.")
        rng = random.Random(opts["seed"])
        call_command("seed_demo", verbosity=0)                       # categories, causes, settings
        cats = {c.name: c for c in Category.objects.all()}
        cat_names = [n for n in SUFFIX if n in cats]
        if not cat_names:
            raise CommandError("No categories found. Run seed_demo first.")
        password = make_password("meem12345")
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend"):   # no email spam
            shops = self.make_sellers(rng, opts["sellers"], cats, cat_names, password)
            shoppers = self.make_shoppers(rng, opts["shoppers"], password)
            made = self.make_orders(rng, opts["orders"], shoppers)
            self.make_money_records(rng, shops)
            self.make_waitlist()
        paid = Order.objects.filter(status="paid").count()
        net = LedgerEntry.objects.aggregate(t=Sum("amount_minor"))["t"] or 0
        self.stdout.write(self.style.SUCCESS(
            f"Done. Shops: {Shop.objects.count()}  Shoppers: {User.objects.filter(role='buyer').count()}  Products: {Product.objects.count()}\n"
            f"Orders made now: {made}  Paid orders total: {paid}  Donations set aside: Rs {net / 100:,.2f}\n"
            "Logins (password meem12345): seller_001..seller_%03d and shopper_001..shopper_%03d" % (opts["sellers"], opts["shoppers"])))

    # ------------------------------------------------------------------ people and shops
    def make_sellers(self, rng, count, cats, cat_names, password):
        shops = []
        for i in range(1, count + 1):
            cat_name = cat_names[i % len(cat_names)]
            username = f"seller_{i:03d}"
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"seller{i:03d}@demo.test", "role": "seller", "password": password})
            name = f"{PREFIX[i % len(PREFIX)]} {SUFFIX[cat_name]}"
            if Shop.objects.filter(name=name).exclude(owner=user).exists():
                name = f"{name} {i}"
            city = CITIES[rng.randrange(len(CITIES))]
            status = Shop.Status.APPROVED
            if i % 17 == 0:
                status = Shop.Status.PENDING            # so you can practise approving shops in the admin
            elif i == 13:
                status = Shop.Status.SUSPENDED
            shop, _ = Shop.objects.get_or_create(owner=user, defaults={
                "name": name, "slug": slugify(name)[:90], "city": city[0], "status": status,
                "tagline": rng.choice(["Made with care.", "Small batch, big heart.", "Honest products for everyday life.", "Family run since 2018."]),
                "story": f"{name} is a Muslim-owned business in {city[0]}. {rng.choice(BLURB)}",
                "payout_note": f"seller{i:03d}@upi"})
            templates = CATALOG[cat_name][:]
            rng.shuffle(templates)
            for title, lo, hi in templates[: rng.randint(4, 7)]:
                title = title.format(c=rng.choice(COLORS))
                rupees = rng.randrange(lo, hi + 1, 10)
                Product.objects.get_or_create(shop=shop, title=title, defaults={
                    "category": cats[cat_name], "slug": slugify(title)[:80] or "product", "price_minor": max(1, (rupees - 1)) * 100,
                    "description": f"{title}. {rng.choice(BLURB)}\nSold by {shop.name}.", "stock": rng.randint(25, 90),
                    "is_active": rng.random() > 0.05})
            shops.append(shop)
        return shops

    def make_shoppers(self, rng, count, password):
        out = []
        for i in range(1, count + 1):
            user, _ = User.objects.get_or_create(
                username=f"shopper_{i:03d}", defaults={"email": f"shopper{i:03d}@demo.test", "role": "buyer", "password": password,
                                                       "first_name": FIRST[i % len(FIRST)], "last_name": LAST[i % len(LAST)]})
            out.append(user)
        return out

    # ------------------------------------------------------------------ orders, donations, fulfilment
    def make_orders(self, rng, count, shoppers):
        now = timezone.now()
        made = 0
        for _ in range(count):
            buyer = rng.choice(shoppers)
            visible = list(Product.objects.visible().filter(stock__gte=3).select_related("shop")[:400])
            if not visible:
                break
            picks = rng.sample(visible, k=min(len(visible), rng.randint(1, 3)))
            lines = []
            for p in picks:
                qty = rng.choice([1, 1, 1, 2, 3])
                lines.append({"product": p, "qty": min(qty, p.stock), "line_total": p.price_minor * min(qty, p.stock)})
            idx = buyer.pk % len(CITIES)
            city, state, pin = CITIES[idx]
            address = {"ship_name": buyer.get_full_name() or buyer.username, "ship_phone": f"98{rng.randint(10000000, 99999999)}",
                       "ship_line1": f"{rng.randint(1, 240)} {rng.choice(['Park Road', 'Lake View', 'Garden Street', 'Masjid Lane', 'Market Road'])}",
                       "ship_line2": "", "ship_city": city, "ship_state": state, "ship_pincode": pin, "ship_country": "India"}
            try:
                order = services.create_order(buyer, lines, address)
            except services.StockError:
                continue
            made += 1
            days_ago = rng.randint(0, 75)
            when = now - timedelta(days=days_ago, hours=rng.randint(0, 22), minutes=rng.randint(0, 59))
            roll = rng.random()
            if roll < 0.06:
                services.cancel_pending(order)
                Order.objects.filter(pk=order.pk).update(created_at=when)
                continue
            if roll < 0.09:
                Order.objects.filter(pk=order.pk).update(created_at=when)      # left unpaid on purpose
                continue
            services.mark_paid(order.pk, "mock", f"seed_{order.number}")
            Order.objects.filter(pk=order.pk).update(created_at=when, paid_at=when + timedelta(minutes=4))
            QuerySet(LedgerEntry).filter(order_id=order.pk).update(created_at=when + timedelta(minutes=4))
            if roll < 0.13:                                                    # refunded
                services.refund_order(order)
                back = min(now, when + timedelta(days=rng.randint(1, 4)))
                QuerySet(LedgerEntry).filter(order_id=order.pk, entry_type="reversal").update(created_at=back)
                continue
            for item in OrderItem.objects.filter(order=order):
                if days_ago > 14:
                    state_ = "delivered" if rng.random() < 0.9 else "shipped"
                elif days_ago > 4:
                    state_ = rng.choice(["shipped", "delivered", "delivered"])
                else:
                    state_ = rng.choice(["placed", "placed", "shipped"])
                fields = {"fulfil_status": state_}
                if state_ != "placed":
                    fields.update(tracking_number=f"DL{rng.randint(10**8, 10**9 - 1)}", shipped_at=when + timedelta(days=1))
                OrderItem.objects.filter(pk=item.pk).update(**fields)
            if rng.random() < 0.03:
                Dispute.objects.create(order=order, user=buyer, reason=rng.choice(REASONS))
        return made

    # ------------------------------------------------------------------ money records
    def make_money_records(self, rng, shops):
        now = timezone.now()
        for shop in shops:
            available = shop.balance()["available"]
            if available > 5000 and rng.random() < 0.7:
                amount = int(available * rng.uniform(0.6, 1.0)) // 100 * 100
                payout = SellerPayout.objects.create(shop=shop, amount_minor=amount, reference=f"UPI{rng.randint(10**9, 10**10 - 1)}", note="Seeded payout")
                SellerPayout.objects.filter(pk=payout.pk).update(created_at=now - timedelta(days=rng.randint(1, 20)))
        for cause in Cause.objects.filter(is_active=True):
            net = cause.ledger_entries.aggregate(t=Sum("amount_minor"))["t"] or 0
            sent = cause.disbursements.aggregate(t=Sum("amount_minor"))["t"] or 0
            if net - sent > 5000:
                Disbursement.objects.create(
                    cause=cause, charity_name=f"{cause.name} Relief Partner (demo)", amount_minor=int((net - sent) * 0.6) // 100 * 100,
                    paid_on=(now - timedelta(days=3)).date(), reference=f"NEFT{rng.randint(10**9, 10**10 - 1)}",
                    note="Demo transfer. Attach a real receipt in the admin.")

    def make_waitlist(self):
        for i in range(1, 41):
            WaitlistEntry.objects.get_or_create(email=f"wait{i:02d}@demo.test", defaults={"interest": "seller" if i % 4 == 0 else "buyer"})
