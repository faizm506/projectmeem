from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("start/<str:number>/", views.start, name="start"),
    path("mock/<str:number>/confirm/", views.mock_confirm, name="mock_confirm"),
    path("razorpay/verify/", views.razorpay_verify, name="razorpay_verify"),
    path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
]
