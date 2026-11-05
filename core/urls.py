from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("waitlist/", views.waitlist, name="waitlist"),
    path("terms/", views.policy("core/terms.html"), name="terms"),
    path("privacy/", views.policy("core/privacy.html"), name="privacy"),
    path("refunds/", views.policy("core/refunds.html"), name="refunds"),
    path("seller-agreement/", views.policy("core/seller_agreement.html"), name="seller_agreement"),
]
