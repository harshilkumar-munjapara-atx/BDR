import secrets

from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsActiveUser

from .models import BusinessListing, EmailVerification


class SendContactEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser]

    def post(self, request):
        try:
            listing = request.user.listing
        except BusinessListing.DoesNotExist:
            return Response({"detail": "No listing found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            contact = listing.contact
        except Exception:
            return Response({"detail": "Listing has no contact information."}, status=status.HTTP_400_BAD_REQUEST)

        if listing.contact_email_verified:
            return Response({"detail": "Contact email is already verified."})

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)

        EmailVerification.objects.filter(listing=listing, verified_at__isnull=True).delete()
        EmailVerification.objects.create(
            listing=listing,
            email_address=contact.primary_email,
            token=token,
            expires_at=expires_at,
        )

        from .tasks import send_verification_email
        send_verification_email.delay(contact.primary_email, token)

        return Response({"detail": f"Verification email sent to {contact.primary_email}."})


class ConfirmContactEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser]

    def post(self, request):
        token = request.data.get("token", "").strip()
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = EmailVerification.objects.get(
                token=token,
                verified_at__isnull=True,
            )
        except EmailVerification.DoesNotExist:
            return Response({"detail": "Invalid or already used token."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.expires_at < timezone.now():
            return Response({"detail": "Token has expired. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.listing.owner != request.user:
            return Response({"detail": "Token does not belong to your listing."}, status=status.HTTP_403_FORBIDDEN)

        verification.verified_at = timezone.now()
        verification.save()

        listing = verification.listing
        listing.contact_email_verified = True
        listing.save()

        return Response({"detail": "Contact email verified successfully."})
