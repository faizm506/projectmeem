from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product

SORTS = {"new": "-created_at", "price_asc": "price_minor", "price_desc": "-price_minor"}


def product_list(request):
    qs = Product.objects.visible().select_related("shop", "category")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "new")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(shop__name__icontains=q))
    if cat:
        qs = qs.filter(category__slug=cat)
    qs = qs.order_by(SORTS.get(sort, "-created_at"))
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "catalog/list.html", {
        "page": page, "categories": Category.objects.all(), "q": q, "active_category": cat,
        "sort": sort, "base_qs": params.urlencode(),
    })


def product_detail(request, pk, slug):
    product = get_object_or_404(Product.objects.visible().select_related("shop", "category"), pk=pk)
    related = Product.objects.visible().filter(category=product.category).exclude(pk=product.pk).select_related("shop", "category")[:4]
    return render(request, "catalog/detail.html", {"product": product, "related": related, "qty_max": min(product.stock, 10)})
