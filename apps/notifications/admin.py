from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["type", "recipient", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    readonly_fields = ["id", "created_at"]
