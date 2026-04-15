import os
from .base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

DATABASES = {
    'default': env.db('DATABASE_URL')
}


CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_PRELOAD = True

# Static files served via S3 in production
# S3 static files — configure on Day 61 (staging deploy)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')

# Sentry error tracking


sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.2,
    send_default_pii=False,   # never send PII to Sentry
)