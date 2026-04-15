from .base import *  # noqa

DEBUG = False
SECRET_KEY = "test-secret-key"  # nosec

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",   # explicit, keeps it clear
        },
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
}

LOGGING: dict = {}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True