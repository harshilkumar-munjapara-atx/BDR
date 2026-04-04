import logging
import secrets
from datetime import timedelta

from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.services import log_action

from .models import PasswordResetToken, RegistrationKey, User, UserEmailVerification
from .permissions import IsAdmin
from .serializers import (
    AdminUserListSerializer,
    AdminUserStatusSerializer,
    RegisterSerializer,
    RegistrationKeyCreateSerializer,
    RegistrationKeySerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)
from .tasks import send_account_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        logger.info("New user registered: email=%s role=%s", user.email, user.role)
        log_action(
            actor=None,
            action="created",
            target=user,
            changed_fields={"email": user.email, "role": user.role},
        )

        token = secrets.token_urlsafe(32)
        UserEmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        send_account_verification_email.delay(user.email, token)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("User logged out: user_id=%s", request.user.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.warning("Logout failed for user_id=%s: %s", request.user.id, e)
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user


class MeUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer
    http_method_names = ["patch"]

    def get_object(self):
        return self.request.user


# --- Admin user management ---

class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        status_filter = self.request.query_params.get("status")
        role_filter = self.request.query_params.get("role")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if role_filter:
            qs = qs.filter(role=role_filter)
        return qs


class AdminUserStatusView(generics.UpdateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminUserStatusSerializer
    queryset = User.objects.all()
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        user = serializer.save()
        logger.info(
            "Admin user_id=%s updated status of user_id=%s to %s",
            self.request.user.id, user.id, user.status,
        )
        log_action(
            actor=self.request.user,
            action="updated",
            target=user,
            changed_fields={"status": user.status},
        )


# --- Registration key management ---

class RegistrationKeyListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = RegistrationKeySerializer

    def get_queryset(self):
        return RegistrationKey.objects.select_related("created_by").order_by("-created_at")


class RegistrationKeyCreateView(generics.CreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = RegistrationKeyCreateSerializer

    def perform_create(self, serializer):
        key = serializer.save()
        logger.info(
            "Admin user_id=%s created registration key: key_value=%s",
            self.request.user.id, key.key_value,
        )
        log_action(
            actor=self.request.user,
            action="key_changed",
            target=key,
            changed_fields={"key_value": key.key_value},
        )


# --- Email verification ---

class SendEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified:
            return Response({"detail": "Email is already verified."})

        UserEmailVerification.objects.filter(user=user, verified_at__isnull=True).delete()

        token = secrets.token_urlsafe(32)
        UserEmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        send_account_verification_email.delay(user.email, token)

        return Response({"detail": f"Verification email sent to {user.email}."})


class ConfirmEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token", "").strip()
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = UserEmailVerification.objects.get(token=token, verified_at__isnull=True)
        except UserEmailVerification.DoesNotExist:
            return Response({"detail": "Invalid or already used token."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.expires_at < timezone.now():
            return Response({"detail": "Token has expired. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.user_id != request.user.pk:
            return Response({"detail": "Token does not belong to your account."}, status=status.HTTP_403_FORBIDDEN)

        verification.verified_at = timezone.now()
        verification.save()

        request.user.email_verified = True
        request.user.save(update_fields=["email_verified"])

        return Response({"detail": "Email verified successfully."})


# --- Password management ---

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")

        if not current_password or not new_password:
            return Response(
                {"detail": "current_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(current_password):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 8:
            return Response(
                {"detail": "New password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        logger.info("User user_id=%s changed their password.", request.user.id)
        return Response({"detail": "Password changed successfully."})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Always return 200 to avoid email enumeration
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If an account with that email exists, a reset link has been sent."})

        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).delete()

        token = secrets.token_urlsafe(32)
        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        send_password_reset_email.delay(user.email, token)

        return Response({"detail": "If an account with that email exists, a reset link has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token", "").strip()
        new_password = request.data.get("new_password", "")

        if not token or not new_password:
            return Response(
                {"detail": "token and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reset = PasswordResetToken.objects.select_related("user").get(token=token, used_at__isnull=True)
        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Invalid or already used token."}, status=status.HTTP_400_BAD_REQUEST)

        if reset.expires_at < timezone.now():
            return Response({"detail": "Token has expired. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        reset.used_at = timezone.now()
        reset.save(update_fields=["used_at"])

        reset.user.set_password(new_password)
        reset.user.save(update_fields=["password"])

        logger.info("User user_id=%s reset their password via token.", reset.user.id)
        return Response({"detail": "Password reset successfully. You can now log in with your new password."})
