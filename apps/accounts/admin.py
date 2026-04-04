from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import RegistrationKey, User


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    list_display = ["email", "name", "role", "status", "created_at"]
    list_filter = ["role", "status"]
    search_fields = ["email", "name"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("name", "phone_number")}),
        ("Access", {"fields": ("role", "status", "email_verified", "registration_key_used")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "password1", "password2", "role"),
        }),
    )


@admin.register(RegistrationKey)
class RegistrationKeyAdmin(ModelAdmin):
    list_display = ["key_value", "is_active", "created_by", "created_at"]
    list_filter = ["is_active"]
    readonly_fields = ["created_at"]
