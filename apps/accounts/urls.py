from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    ConfirmEmailVerificationView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeUpdateView,
    MeView,
    RegisterView,
    ResetPasswordView,
    SendEmailVerificationView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("me/update/", MeUpdateView.as_view(), name="auth-me-update"),
    path("send-verification/", SendEmailVerificationView.as_view(), name="auth-send-verification"),
    path("verify-email/", ConfirmEmailVerificationView.as_view(), name="auth-verify-email"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
]
