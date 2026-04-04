import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_LISTING_SUBMITTED = "new_listing_submitted", "New Listing Submitted"
        NEW_USER_REGISTERED = "new_user_registered", "New User Registered"
        LISTING_FLAGGED = "listing_flagged", "Listing Flagged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        limit_choices_to={"role": "admin"},
    )
    type = models.CharField(max_length=50, choices=Type.choices)
    reference_id = models.UUIDField(null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} → {self.recipient.email}"
