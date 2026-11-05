from django.conf import settings

from .models import SiteSetting


def site(request):
    return {"site_setting": SiteSetting.get(), "SITE_NAME": settings.SITE_NAME}
