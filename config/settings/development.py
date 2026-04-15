from .base import *

#CSRF_TRUSTED_ORIGIN

DEBUG = True 

#SECRET_KEY = 'django-insecure-7@!g#61an9@04)t3-a4#&psdz@6t)cl((ua%iwk-cb3x%9j40='

SECRET_KEY = env("SECRET_KEY", default='iypDoBKT9Sbb5C8a3GnyQUwpvKnzk8SQVU0QpltxdsuCqb3F48')

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
}

# Django Debug Toolbar (optional but useful)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False