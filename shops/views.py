from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from catalog.models import Product
from core import emails
from orders.models import Order, OrderItem

from .forms import ProductForm, ShipForm, ShopForm
from .models import Shop


def seller_required(view):
    """Needs a login and an existing shop. Passes the shop to the view."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        shop = Shop.objects.filter(owner=request.user).first()
        if shop is None:
            messages.info(request, "Open your shop first.")
            return redirect("shops:create")
        return view(request, shop, *args, **kwargs)

    return wrapper


def unique_slug(name):
    base = slugify(name)[:70] or "shop"
    slug, n = base, 2
    while Shop.objects.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def shop_list(request):
    shops = Shop.objects.filter(status=Shop.Status.APPROVED)
    return render(request, "shops/list.html", {"shops": shops})


def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug, status=Shop.Status.APPROVED)
    products = Product.objects.visible().filter(shop=shop).select_related("category")
    return render(request, "shops/detail.html", {"shop": shop, "products": products})


@login_required
def shop_create(request):
    if Shop.objects.filter(owner=request.user).exists():
        return redirect("shops:dashboard")
    form = ShopForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        shop = form.save(commit=False)
        shop.owner = request.user
        shop.slug = unique_slug(shop.name)
        shop.save()
        request.user.role = "seller"
        request.user.save(update_fields=["role"])
        emails.shop_submitted(shop)
        messages.success(request, "Your shop is created. We will review it and email you soon.")
        return redirect("shops:dashboard")
    return render(request, "shops/form.html", {"form": form, "title": "Open your shop", "intro": "Tell us about your brand. We review every shop by hand to keep MEEM a trusted space."})


@seller_required
def shop_edit(request, shop):
    form = ShopForm(request.POST or None, request.FILES or None, instance=shop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Shop updated.")
        return redirect("shops:dashboard")
    return render(request, "shops/form.html", {"form": form, "title": "Edit your shop", "intro": ""})


@seller_required
def dashboard(request, shop):
    items = OrderItem.objects.filter(shop=shop, order__status=Order.Status.PAID).select_related("order")
    context = {
        "shop": shop,
        "balance": shop.balance(),
        "products": Product.objects.filter(shop=shop).select_related("category").order_by("-created_at"),
        "recent_items": items.order_by("-order__paid_at")[:8],
        "order_count": items.values("order_id").distinct().count(),
        "payouts": shop.payouts.all()[:5],
    }
    return render(request, "shops/dashboard.html", context)


@seller_required
def product_new(request, shop):
    if not shop.is_approved:
        messages.info(request, "You can add products once your shop is approved.")
        return redirect("shops:dashboard")
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.shop = shop
        product.slug = slugify(product.title)[:80] or "product"
        product.save()
        messages.success(request, "Product added.")
        return redirect("shops:dashboard")
    return render(request, "shops/form.html", {"form": form, "title": "Add a product", "intro": ""})


@seller_required
def product_edit(request, shop, pk):
    product = get_object_or_404(Product, pk=pk, shop=shop)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.slug = slugify(obj.title)[:80] or "product"
        obj.save()
        messages.success(request, "Product updated.")
        return redirect("shops:dashboard")
    return render(request, "shops/form.html", {"form": form, "title": "Edit product", "intro": ""})


@seller_required
def orders(request, shop):
    items = OrderItem.objects.filter(shop=shop, order__status=Order.Status.PAID).select_related("order").order_by("-order__paid_at")
    page = Paginator(items, 15).get_page(request.GET.get("page"))
    return render(request, "shops/orders.html", {"shop": shop, "page": page, "ship_form": ShipForm()})


@seller_required
@require_POST
def item_ship(request, shop, pk):
    item = get_object_or_404(OrderItem, pk=pk, shop=shop, order__status=Order.Status.PAID)
    form = ShipForm(request.POST)
    if item.fulfil_status == OrderItem.Fulfil.PLACED and form.is_valid():
        item.fulfil_status = OrderItem.Fulfil.SHIPPED
        item.tracking_number = form.cleaned_data["tracking_number"]
        item.shipped_at = timezone.now()
        item.save(update_fields=["fulfil_status", "tracking_number", "shipped_at"])
        emails.item_shipped(item)
        messages.success(request, "Marked as shipped. The buyer has been emailed.")
    return redirect("shops:orders")


@seller_required
@require_POST
def item_delivered(request, shop, pk):
    item = get_object_or_404(OrderItem, pk=pk, shop=shop, order__status=Order.Status.PAID)
    if item.fulfil_status == OrderItem.Fulfil.SHIPPED:
        item.fulfil_status = OrderItem.Fulfil.DELIVERED
        item.save(update_fields=["fulfil_status"])
        messages.success(request, "Marked as delivered. The earning is now available for payout.")
    return redirect("shops:orders")
