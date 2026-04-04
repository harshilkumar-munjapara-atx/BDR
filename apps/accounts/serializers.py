from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import RegistrationKey, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.status == User.Status.SUSPENDED:
            raise serializers.ValidationError("Your account has been suspended.")
        data["role"] = self.user.role
        data["name"] = self.user.name
        return data


class RegisterSerializer(serializers.ModelSerializer):
    registration_key = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "name", "phone_number", "password", "registration_key"]

    def validate_registration_key(self, value):
        try:
            key = RegistrationKey.objects.get(key_value=value, is_active=True)
        except RegistrationKey.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired registration key.")
        return key

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        key = validated_data.pop("registration_key")
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Role.INVESTOR, registration_key_used=key)
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "phone_number", "role", "status", "email_verified", "created_at"]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "phone_number"]


class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "status", "created_at"]
        read_only_fields = fields


class AdminUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["status"]

    def validate_status(self, value):
        if value not in [User.Status.ACTIVE, User.Status.SUSPENDED]:
            raise serializers.ValidationError("Invalid status.")
        return value


class RegistrationKeySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)

    class Meta:
        model = RegistrationKey
        fields = ["id", "key_value", "is_active", "notes", "created_by_name", "created_at"]
        read_only_fields = ["id", "is_active", "created_by_name", "created_at"]


class RegistrationKeyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationKey
        fields = ["key_value", "notes"]

    def validate_key_value(self, value):
        if RegistrationKey.objects.filter(key_value=value).exists():
            raise serializers.ValidationError("This key value already exists.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["is_active"] = True
        return super().create(validated_data)
