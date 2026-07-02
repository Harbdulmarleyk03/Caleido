from .production import *  # noqa

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Belt-and-suspenders: if SENTRY_DSN ever ends up set in a local .env used
# with docker-compose, tag those events distinctly rather than let them
# mix into real production incidents. The primary control is still "don't
# set SENTRY_DSN locally" — this is the fallback, not the plan.
SENTRY_ENVIRONMENT = "docker-local"
