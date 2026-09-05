import logging
import os

import dj_database_url

from canidoit.settings.base import *  # noqa
from canidoit.settings.base import DATABASES, LOGGING, MIDDLEWARE
from canidoit.utils import deep_merge

logger = logging.getLogger(__name__)

DEBUG = False

env = os.environ.copy()

ALLOWED_HOSTS = ["localhost:8000", "localhost", *env["ALLOWED_HOSTS"].split(",")]

BASE_URL = env["BASE_URL"]

CSRF_TRUSTED_ORIGINS = [
    BASE_URL,
]

if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dict(dj_database_url.config())
    DATABASES["default"].update(
        {
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "pool": {
                    "min_size": 4,
                    "max_size": 16,
                    "timeout": 10,
                    "max_lifetime": 1800,
                    "max_idle": 300,
                },
            },
        }
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECRET_KEY = env["SECRET_KEY"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

for smtp_var in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "SMTP_PORT"):
    if smtp_var not in env:
        logger.warning(f"Missing SMTP environment variable: {smtp_var}")

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "HOST": env.get("SMTP_HOST", "localhost"),
        "USER": env.get("SMTP_USER", ""),
        "PASSWORD": env.get("SMTP_PASS", ""),
        "PORT": int(env.get("SMTP_PORT", "25")),
        "USE_TLS": (env.get("SMTP_TLS", "True") or "True") != "False",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default",
    },
}

LOGGING = deep_merge(
    LOGGING,
    {
        "formatters": {
            "verbose": {
                "format": "{levelname}: ({module}) {message}",
            },
        },
    },
)
