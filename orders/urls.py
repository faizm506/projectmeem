from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("", views.order_list, name="list"),
    path("checkout/", views.checkout, name="checkout"),
    path("<str:number>/", views.order_detail, name="detail"),
    path("<str:number>/report/", views.dispute_create, name="dispute"),
]
