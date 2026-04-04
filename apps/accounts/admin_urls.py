from django.urls import path

from .views import AdminUserListView, AdminUserStatusView, RegistrationKeyCreateView, RegistrationKeyListView

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<uuid:pk>/status/", AdminUserStatusView.as_view(), name="admin-user-status"),
    path("registration-keys/", RegistrationKeyListView.as_view(), name="admin-key-list"),
    path("registration-keys/create/", RegistrationKeyCreateView.as_view(), name="admin-key-create"),
]
