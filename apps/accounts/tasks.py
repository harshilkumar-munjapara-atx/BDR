from celery import shared_task
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, to_email: str, token: str):
    try:
        send_mail(
            subject="Reset your password — BDR",
            message=(
                "You requested a password reset for your BDR account.\n\n"
                f"Reset token: {token}\n\n"
                "This token expires in 1 hour. Use it at:\n"
                f'POST /api/auth/reset-password/ with {{"token": "{token}", "new_password": "..."}}\n\n'
                "If you did not request this, you can safely ignore this email."
            ),
            from_email=None,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_account_verification_email(self, to_email: str, token: str):
    try:
        send_mail(
            subject="Verify your email address — BDR",
            message=(
                "Welcome to BDR! Please verify your email address.\n\n"
                f"Verification token: {token}\n\n"
                "This token expires in 24 hours. Use it at:\n"
                f'POST /api/auth/verify-email/ with {{"token": "{token}"}}'
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
