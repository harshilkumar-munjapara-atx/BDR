from django.urls import path

from .views import NotificationListView, NotificationMarkAllReadView, NotificationMarkReadView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="admin-notification-list"),
    path("notifications/<uuid:pk>/read/", NotificationMarkReadView.as_view(), name="admin-notification-read"),
    path("notifications/read-all/", NotificationMarkAllReadView.as_view(), name="admin-notification-read-all"),
]
