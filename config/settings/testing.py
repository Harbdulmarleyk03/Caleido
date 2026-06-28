from .base import *  # noqa

DEBUG = False
SECRET_KEY = "test-secret-key"  # nosec

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

ICAL_UID_DOMAIN = "test.caleido.com"  # Domain used for generating unique identifiers in iCal files

MIGRATION_MODULES = {}  # use real migrations, not mocked ones

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

LOGGING: dict = {}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# config/settings/testing.py
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # inherit base settings
    'DEFAULT_THROTTLE_CLASSES': [],  # disable all throttling in tests
    'DEFAULT_THROTTLE_RATES': {},
}

CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'