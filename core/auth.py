from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from . import security


class LockoutBackend(ModelBackend):
    """Normal username and password login, but refuses to even check the password while the account/IP is locked.
    Protects the website login and the admin login in one place."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is not None and username and security.is_throttled(request, username):
            raise PermissionDenied
        return super().authenticate(request, username=username, password=password, **kwargs)
