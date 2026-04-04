from celery import shared_task
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, to_email: str, token: str):
    try:
        send_mail(
            subject="Verify your listing contact email — BDR",
            message=(
                "Please verify your listing's contact email address.\n\n"
                f"Verification token: {token}\n\n"
                "This token expires in 24 hours. Use it at:\n"
                f'POST /api/listings/mine/verify-email/ with {{"token": "{token}"}}'
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[to_email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
