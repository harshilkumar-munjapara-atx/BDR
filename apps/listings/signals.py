from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BusinessListing


@receiver(post_save, sender=BusinessListing)
def notify_admin_on_pending(sender, instance, created, **kwargs):
    """Create an admin notification when a listing moves to pending."""
    if not created and instance.status == BusinessListing.Status.PENDING:
        from apps.accounts.models import User
        from apps.notifications.models import Notification

        admins = User.objects.filter(role=User.Role.ADMIN, status="active")
        notifications = [
            Notification(
                recipient=admin,
                type=Notification.Type.NEW_LISTING_SUBMITTED,
                reference_id=instance.id,
                message=f"New listing submitted for review: {getattr(instance, 'identity', None) and instance.identity.company_name or instance.id}",
            )
            for admin in admins
        ]
        if notifications:
            Notification.objects.bulk_create(notifications, ignore_conflicts=True)
