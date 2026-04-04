import logging

from .models import AuditLog

logger = logging.getLogger("apps.audit")


def log_action(actor, action: str, target, changed_fields: dict = None):
    """Write an audit log entry. Safe to call from anywhere — never raises."""
    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=type(target).__name__,
            target_id=str(target.pk),
            changed_fields=changed_fields or {},
        )
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
