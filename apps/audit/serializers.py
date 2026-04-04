from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", default=None)

    class Meta:
        model = AuditLog
        fields = ["id", "actor_email", "action", "target_type", "target_id", "changed_fields", "timestamp"]
        read_only_fields = fields
