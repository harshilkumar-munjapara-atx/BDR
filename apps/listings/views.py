from django.core.cache import cache
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveUser
from apps.audit.services import log_action

from .models import BusinessListing
from .serializers import (
    ListingDetailSerializer,
    ListingSubmitSerializer,
    ListingWriteSerializer,
)


class MyListingView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser]

    def _get_listing(self, user):
        try:
            return BusinessListing.objects.select_related(
                "identity", "contact", "commercial"
            ).prefetch_related(
                "offices", "products", "key_people"
            ).get(owner=user, is_deleted=False)
        except BusinessListing.DoesNotExist:
            return None

    def get(self, request):
        listing = self._get_listing(request.user)
        if not listing:
            return Response({"detail": "No listing found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ListingDetailSerializer(listing).data)

    def post(self, request):
        if BusinessListing.objects.filter(owner=request.user).exists():
            return Response(
                {"detail": "You already have a listing. Edit your existing listing instead."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = ListingWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        log_action(actor=request.user, action="created", target=listing)
        return Response(ListingDetailSerializer(listing).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        listing = self._get_listing(request.user)
        if not listing:
            return Response({"detail": "No listing found."}, status=status.HTTP_404_NOT_FOUND)
        if listing.status == BusinessListing.Status.ARCHIVED:
            return Response({"detail": "Archived listings cannot be edited."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ListingWriteSerializer(listing, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        listing = serializer.save()
        log_action(actor=request.user, action="updated", target=listing)
        cache.delete_pattern("search:*")  # Invalidate search cache on edit
        return Response(ListingDetailSerializer(listing).data)

    def delete(self, request):
        listing = self._get_listing(request.user)
        if not listing:
            return Response({"detail": "No listing found."}, status=status.HTTP_404_NOT_FOUND)
        listing.status = BusinessListing.Status.ARCHIVED
        listing.is_deleted = True
        listing.deleted_at = timezone.now()
        listing.save()
        log_action(actor=request.user, action="deleted", target=listing)
        cache.delete_pattern("search:*")
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyListingSubmitView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsActiveUser]
    serializer_class = ListingSubmitSerializer
    http_method_names = ["post"]

    def get_object(self):
        try:
            return self.request.user.listing
        except BusinessListing.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("No listing found.")

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        listing = serializer.save()
        log_action(actor=self.request.user, action="updated", target=listing, changed_fields={"status": "pending"})


class ListingPublicDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListingDetailSerializer
    lookup_field = "identity__slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return BusinessListing.objects.filter(
            status=BusinessListing.Status.PUBLISHED,
            is_deleted=False,
        ).select_related("identity", "contact", "commercial").prefetch_related(
            "offices", "products", "key_people"
        )
