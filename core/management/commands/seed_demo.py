from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from accounts.models import User
from catalog.models import Category, Product
from core.models import SiteSetting
from donations.models import Cause
from shops.models import Shop

CAUSES = [
    ("Gaza", "Food, medicine and shelter for families in Gaza.", 2),
    ("Yemen", "Clean water and emergency relief in Yemen.", 1),
    ("Sudan", "Support for displaced families in Sudan.", 1),
    ("Wherever it's needed", "Flexible help where it is needed most.", 1),
]
CATEGORIES = [
    ("Modest fashion", "Abayas, hijabs and everyday wear.", "shirt", "g"),
    ("Halal skincare", "Gentle, honest ingredients.", "drop", "s"),
    ("Islamic books", "Quran, seerah and stories for every age.", "book", "d"),
    ("Tech", "Gadgets and apps from Muslim founders.", "tech", "o"),
    ("Home", "Calm, beautiful pieces for your space.", "home", "s"),
    ("Gifts", "For Eid, weddings and just because.", "gift", "g"),
]
SELLERS = [
    ("seller_amina", "Noor Modest Wear", "Everyday modest fashion, made with care.", "Ahmedabad", "Modest fashion", [
        ("Linen Everyday Abaya", "Breathable linen abaya with deep pockets and a relaxed fit.", 249900, 12),
        ("Cotton Hijab Set (3 pack)", "Soft jersey hijabs in sage, sand and cream.", 79900, 30),
        ("Eid Embroidered Kaftan", "Hand-finished embroidery on light chiffon.", 419900, 6)]),
    ("seller_yusuf", "Barakah Botanicals", "Halal, plant-based skincare.", "Hyderabad", "Halal skincare", [
        ("Rose Water Toner", "Alcohol-free rose water toner, 100 ml.", 34900, 40),
        ("Black Seed Face Oil", "Cold-pressed nigella oil blend, 30 ml.", 59900, 25),
        ("Argan Hand Cream", "Rich, non-greasy hand cream, 75 g.", 29900, 50)]),
    ("seller_noor", "Iqra Books", "Books that feed the heart and mind.", "Mumbai", "Islamic books", [
        ("Stories of the Prophets (Kids)", "Illustrated hardcover for ages 5 to 9.", 69900, 20),
        ("Daily Duas Pocket Edition", "Arabic with transliteration and meaning.", 24900, 60),
        ("Seerah in Short", "A gentle, well-researched introduction.", 49900, 15)]),
]


class Command(BaseCommand):
    help = "Create demo data (causes, categories, three approved shops, products, test accounts). Development only."

    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError("seed_demo creates accounts with a known password. It only runs with DEBUG=1.")
        SiteSetting.get()
        for name, desc, weight in CAUSES:
            Cause.objects.get_or_create(slug=slugify(name), defaults={"name": name, "description": desc, "weight": weight,
                                                                    "partner_charity": "Partner charity (add in admin)"})
        cats = {}
        for i, (name, blurb, icon, tone) in enumerate(CATEGORIES):
            cats[name], _ = Category.objects.get_or_create(slug=slugify(name), defaults={"name": name, "blurb": blurb, "icon": icon, "tone": tone, "position": i})
        pw = "meem12345"
        buyer, made = User.objects.get_or_create(username="demo_buyer", defaults={"email": "buyer@demo.test", "role": "buyer"})
        if made:
            buyer.set_password(pw)
            buyer.save()
        for username, shop_name, tagline, city, cat_name, products in SELLERS:
            user, made = User.objects.get_or_create(username=username, defaults={"email": f"{username}@demo.test", "role": "seller"})
            if made:
                user.set_password(pw)
                user.save()
            shop, _ = Shop.objects.get_or_create(owner=user, defaults={
                "name": shop_name, "slug": slugify(shop_name), "tagline": tagline, "city": city,
                "story": f"{shop_name} is a small Muslim-owned brand in {city}.", "status": Shop.Status.APPROVED})
            for title, desc, price, stock in products:
                Product.objects.get_or_create(shop=shop, title=title, defaults={
                    "category": cats[cat_name], "slug": slugify(title)[:80], "description": desc, "price_minor": price, "stock": stock})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Test logins (password meem12345): demo_buyer, seller_amina, seller_yusuf, seller_noor"))
