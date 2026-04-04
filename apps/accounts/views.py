import logging

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.services import log_action

from .models import User
from .permissions import IsAdmin

logger = logging.getLogger(__name__)
from .serializers import (
    AdminUserListSerializer,
    AdminUserStatusSerializer,
    RegisterSerializer,
    RegistrationKeyCreateSerializer,
    RegistrationKeySerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)


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
        from .models import RegistrationKey
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
