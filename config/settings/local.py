from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Override email to console in local dev (comment out to test real Gmail)
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("ACCESS_TOKEN_LIFETIME_MINUTES", default=400000, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS": True,
}