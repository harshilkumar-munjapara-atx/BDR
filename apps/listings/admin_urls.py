from django.urls import path

from .admin_views import (
    AdminListingArchiveView,
    AdminListingDetailView,
    AdminListingListView,
    AdminListingPublishView,
)

urlpatterns = [
    path("listings/", AdminListingListView.as_view(), name="admin-listing-list"),
    path("listings/<uuid:pk>/", AdminListingDetailView.as_view(), name="admin-listing-detail"),
    path("listings/<uuid:pk>/publish/", AdminListingPublishView.as_view(), name="admin-listing-publish"),
    path("listings/<uuid:pk>/archive/", AdminListingArchiveView.as_view(), name="admin-listing-archive"),
]
