from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "tone", "position")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "shop", "category", "price_minor", "stock", "is_active")
    list_filter = ("category", "is_active", "shop")
    search_fields = ("title", "shop__name")
