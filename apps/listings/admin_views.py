from django.core.cache import cache
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.audit.services import log_action

from .models import BusinessListing
from .serializers import (
    AdminListingListSerializer,
    AdminPublishSerializer,
    ListingDetailSerializer,
    ListingWriteSerializer,
)


class AdminListingListView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ListingWriteSerializer
        return AdminListingListSerializer

    def get_queryset(self):
        qs = BusinessListing.objects.select_related(
            "identity", "owner"
        ).order_by("-created_at")
        # Admin can filter to see deleted listings explicitly via ?is_deleted=true
        show_deleted = self.request.query_params.get("is_deleted") == "true"
        if not show_deleted:
            qs = qs.filter(is_deleted=False)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        listing = serializer.save()
        log_action(actor=self.request.user, action="created", target=listing)


class AdminListingDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdmin]
    queryset = BusinessListing.objects.select_related(
        "identity", "contact", "commercial"
    ).prefetch_related("offices", "products", "key_people")

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return ListingWriteSerializer
        return ListingDetailSerializer

    def perform_update(self, serializer):
        listing = serializer.save()
        log_action(actor=self.request.user, action="updated", target=listing)
        cache.delete_pattern("search:*")


class AdminListingPublishView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            listing = BusinessListing.objects.get(pk=pk)
        except BusinessListing.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get("action")  # "publish" or "unpublish"
        if action == "publish":
            listing.status = BusinessListing.Status.PUBLISHED
            listing.published_at = timezone.now()
        elif action == "unpublish":
            listing.status = BusinessListing.Status.DRAFT
            listing.published_at = None
        else:
            return Response({"detail": "action must be 'publish' or 'unpublish'."}, status=status.HTTP_400_BAD_REQUEST)

        listing.save()
        log_action(
            actor=request.user,
            action="published" if action == "publish" else "updated",
            target=listing,
            changed_fields={"status": listing.status},
        )
        cache.delete_pattern("search:*")
        return Response(AdminListingListSerializer(listing).data)


class AdminListingArchiveView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            listing = BusinessListing.objects.get(pk=pk)
        except BusinessListing.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        listing.status = BusinessListing.Status.ARCHIVED
        listing.save()
        log_action(actor=request.user, action="archived", target=listing, changed_fields={"status": "archived"})
        cache.delete_pattern("search:*")
        return Response(status=status.HTTP_204_NO_CONTENT)
