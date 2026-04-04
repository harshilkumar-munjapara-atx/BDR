from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        unread_only = self.request.query_params.get("unread")
        if unread_only == "true":
            qs = qs.filter(is_read=False)
        return qs[:50]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        data = {
            "unread_count": unread_count,
            "results": NotificationSerializer(qs, many=True).data,
        }
        return Response(data)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
