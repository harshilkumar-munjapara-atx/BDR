from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.listings.urls")),
    path("api/admin/", include("apps.listings.admin_urls")),
    path("api/admin/", include("apps.accounts.admin_urls")),
    path("api/admin/", include("apps.notifications.urls")),
    path("api/admin/", include("apps.imports.urls")),
    path("api/admin/", include("apps.audit.urls")),
]
