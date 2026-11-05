from django.db import models
from django.urls import reverse


class Category(models.Model):
    ICONS = [("shirt", "Shirt"), ("drop", "Drop"), ("book", "Book"), ("tech", "Phone"), ("home", "Home"),
             ("gift", "Gift"), ("heart", "Heart"), ("moon", "Moon")]
    TONES = [("g", "Green"), ("s", "Sand"), ("o", "Gold"), ("d", "Dark green")]

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    blurb = models.CharField(max_length=140, blank=True)
    icon = models.CharField(max_length=10, choices=ICONS, default="heart")
    tone = models.CharField(max_length=1, choices=TONES, default="g")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(is_active=True, shop__status="approved")


class Product(models.Model):
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, blank=True)
    description = models.TextField(blank=True)
    price_minor = models.PositiveIntegerField(help_text="In paise (100 paise = 1 rupee).")
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:detail", args=[self.pk, self.slug or "product"])

    @property
    def in_stock(self):
        return self.stock > 0
