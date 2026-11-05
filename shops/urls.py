from django.urls import path

from . import views

app_name = "shops"
urlpatterns = [
    path("", views.shop_list, name="list"),
    path("open/", views.shop_create, name="create"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/edit/", views.shop_edit, name="edit"),
    path("dashboard/products/new/", views.product_new, name="product_new"),
    path("dashboard/products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("dashboard/orders/", views.orders, name="orders"),
    path("dashboard/orders/<int:pk>/ship/", views.item_ship, name="item_ship"),
    path("dashboard/orders/<int:pk>/delivered/", views.item_delivered, name="item_delivered"),
    path("<slug:slug>/", views.shop_detail, name="detail"),
]
