import django_stubs_ext

from canidoit.settings.base import *  # noqa
from canidoit.settings.base import BASE_DIR, INSTALLED_APPS, LOGGING, MIDDLEWARE
from canidoit.utils import deep_merge

django_stubs_ext.monkeypatch()

SECRET_KEY = "django-insecure-&vwatohgdz+5zfxt0oizt%3q2+ug6f-cidcb0^x^6@%h4mo^*1"

DEBUG = True

INSTALLED_APPS += [
    "django_browser_reload",
    "debug_toolbar",
    "zeal",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "zeal.middleware.zeal_middleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

ALLOWED_HOSTS = ["*"]

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

INTERNAL_IPS = [
    "127.0.0.1",
]

LOGGING = deep_merge(
    LOGGING,
    {
        "root": {
            "level": "DEBUG",
        },
    },
)

CSP_DEFAULT_SRC = None
CSP_STYLE_SRC = None
CSP_FONT_SRC = None
CSP_IMG_SRC = None

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
