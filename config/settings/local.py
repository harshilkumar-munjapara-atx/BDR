from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Override email to console in local dev (comment out to test real Gmail)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
