from rest_framework import generics

from apps.accounts.permissions import IsAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor").order_by("-timestamp")
        target_type = self.request.query_params.get("target_type")
        target_id = self.request.query_params.get("target_id")
        action = self.request.query_params.get("action")
        if target_type:
            qs = qs.filter(target_type__iexact=target_type)
        if target_id:
            qs = qs.filter(target_id=target_id)
        if action:
            qs = qs.filter(action=action)
        return qs
