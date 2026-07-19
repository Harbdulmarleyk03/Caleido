from .base import *  # noqa

DEBUG = False
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")


# Upstash Redis requires TLS (rediss://), and Celery's Redis transport
# needs explicit ssl_cert_reqs when using rediss:// or it raises ValueError.
# CERT_NONE skips cert verification — acceptable here since Upstash manages
# its own cert and this is a trusted managed connection, not raw internet traffic.
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": "CERT_NONE"}
CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": "CERT_NONE"}

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_PRELOAD = True

# Static files served via S3 in production
# S3 static files — configure on Day 61 (staging deploy)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')

# ---------------------------------------------------------------------------
# Sentry error tracking
#
# Guarded entirely by SENTRY_DSN (declared in base.py, default ""). Any
# environment that doesn't set it — dev, testing, CI — never calls init().
# docker.py inherits this file via `from .production import *`, so local
# Docker is only ever protected because its .env doesn't set SENTRY_DSN;
# SENTRY_ENVIRONMENT exists as a second line of defense so that if it *is*
# ever set locally, those events land tagged "docker-local" in Sentry
# instead of silently mixing into real production incidents.
# ---------------------------------------------------------------------------
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    # PII fields that must never leave this process. Explicit denylist,
    # not a generic recursive scrubber — easier to audit, easier to extend
    # deliberately when a new endpoint introduces a new sensitive field.
    _SENSITIVE_HEADERS = {"authorization", "cookie"}
    _SENSITIVE_BODY_KEYS = {
        "token",  # signed cancel/reschedule token — a bearer credential
        "password",
        "invitee_email",
        "invitee_name",
        "invitee_notes",
        "email",
    }

    def _scrub_mapping(mapping):
        if not isinstance(mapping, dict):
            return mapping
        for key in list(mapping.keys()):
            if key.lower() in _SENSITIVE_HEADERS or key.lower() in _SENSITIVE_BODY_KEYS:
                mapping[key] = "[Filtered]"
        return mapping

    def before_send(event, hint):
        request = event.get("request")
        if request:
            _scrub_mapping(request.get("headers"))
            _scrub_mapping(request.get("cookies"))
            _scrub_mapping(request.get("data"))
            # query_string is a raw string on some SDK versions, a list of
            # tuples on others — only scrub the dict form; leave the raw
            # string case alone rather than guess at parsing it here.
            if isinstance(request.get("query_string"), dict):
                _scrub_mapping(request.get("query_string"))

        # send_default_pii=False already stops Sentry auto-attaching user
        # data, but strip it explicitly too — defense in depth, and it
        # documents the intent for the next engineer reading this file.
        event.pop("user", None)

        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(monitor_beat_tasks=False),
        ],
        # Fraction of requests/tasks fully traced for performance data.
        # 0.2 is a cost/visibility trade-off, not a correctness setting —
        # revisit once real traffic volume and Sentry quota are known.
        traces_sample_rate=0.2,
        send_default_pii=False,
        before_send=before_send,
    )

    # The ">500ms" alert is NOT expressed here. This SDK only emits the
    # performance trace data; the alert rule that fires on p95/threshold
    # is configured in the Sentry dashboard (Alerts > Performance) against
    # the traces this init() call starts producing. That's a deploy-time
    # manual step, not code — don't go looking for it in this repo.
