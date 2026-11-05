"""Small, dependency-free security helpers: client IP, rate limits, login lockout."""
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

LOGIN_MAX_FAILS = 5
LOGIN_WINDOW = 15 * 60


def client_ip(request):
    """Real client IP. Only trusts X-Forwarded-For when TRUST_PROXY_HEADERS=1 (set it only behind a proxy you control)."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "unknown")[:45]


def _bump(key, window):
    """Count an event for `key` inside a fixed window. Returns the new count."""
    now = time.time()
    k = "rl:" + key
    data = cache.get(k)
    if not data or data[1] <= now:
        data = [0, now + window]
    data[0] += 1
    cache.set(k, data, max(1, int(data[1] - now)))
    return data[0]


def _count(key):
    data = cache.get("rl:" + key)
    return data[0] if data and data[1] > time.time() else 0


def hit(key, limit, window):
    """Record an event; True when the caller is now over the limit."""
    return _bump(key, window) > limit


def throttle(scope, limit, window, methods=("POST",)):
    """View decorator: max `limit` requests per `window` seconds per client IP."""
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method in methods and hit(f"{scope}:{client_ip(request)}", limit, window):
                return render(request, "429.html", status=429)
            return view(request, *args, **kwargs)
        return wrapper
    return deco


# ---- login lockout: 5 failures per username+IP, or 40 per IP, then a 15 minute pause
def _login_keys(request, username):
    ip = client_ip(request)
    return f"fail:{(username or '').strip().lower()[:150]}:{ip}", f"failip:{ip}"


def is_throttled(request, username):
    user_key, ip_key = _login_keys(request, username)
    return _count(user_key) >= LOGIN_MAX_FAILS or _count(ip_key) >= LOGIN_MAX_FAILS * 8


def add_failure(request, username):
    user_key, ip_key = _login_keys(request, username)
    _bump(user_key, LOGIN_WINDOW)
    _bump(ip_key, LOGIN_WINDOW)


def clear_failures(request, username):
    user_key, _ = _login_keys(request, username)
    cache.delete("rl:" + user_key)
