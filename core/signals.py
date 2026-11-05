import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import security

log = logging.getLogger("meem.security")


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    if request is None:
        return
    username = (credentials or {}).get("username", "")
    security.add_failure(request, username)
    log.warning("Failed login for %r from %s", str(username)[:60], security.client_ip(request))


@receiver(user_logged_in)
def on_login_ok(sender, request, user, **kwargs):
    if request is not None:
        security.clear_failures(request, user.get_username())
