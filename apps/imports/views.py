import os

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.audit.services import log_action
from apps.listings.models import BusinessListing
from apps.listings.slug_utils import generate_unique_slug

from .parser import parse_excel


class ExcelPreviewView(APIView):
    """
    POST /api/admin/listings/import/preview/
    Accepts multipart Excel file, returns validation report without writing anything.
    """
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not file_obj.name.endswith((".xlsx", ".xls")):
            return Response({"detail": "Only .xlsx / .xls files are accepted."}, status=status.HTTP_400_BAD_REQUEST)

        rows, global_errors = parse_excel(file_obj.read())

        valid_rows = [r for r in rows if r.is_valid]
        error_rows = [
            {"row": r.row_number, "errors": r.errors, "company_name": r.data.get("identity", {}).get("company_name", "")}
            for r in rows if not r.is_valid
        ]

        return Response({
            "total_rows": len(rows),
            "valid_rows": len(valid_rows),
            "error_rows": error_rows,
            "global_errors": global_errors,
            "can_import": not global_errors and len(valid_rows) > 0,
        })


class ExcelConfirmImportView(APIView):
    """
    POST /api/admin/listings/import/confirm/
    Accepts multipart Excel file, writes valid rows as draft listings.
    """
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        if not file_obj.name.endswith((".xlsx", ".xls")):
            return Response({"detail": "Only .xlsx / .xls files are accepted."}, status=status.HTTP_400_BAD_REQUEST)

        rows, global_errors = parse_excel(file_obj.read())
        if global_errors:
            return Response({"detail": "File has errors.", "global_errors": global_errors}, status=status.HTTP_400_BAD_REQUEST)

        valid_rows = [r for r in rows if r.is_valid]
        if not valid_rows:
            return Response({"detail": "No valid rows to import."}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        skipped_count = 0

        for row in valid_rows:
            try:
                listing = _create_listing_from_row(row.data, actor=request.user)
                if listing:
                    created_count += 1
                    log_action(actor=request.user, action="created", target=listing)
                else:
                    skipped_count += 1
            except Exception:
                skipped_count += 1

        return Response({
            "created": created_count,
            "skipped": skipped_count,
            "message": f"Import complete. {created_count} listings created as draft.",
        }, status=status.HTTP_201_CREATED)


def _create_listing_from_row(data: dict, actor) -> BusinessListing | None:
    from apps.listings.models import (
        ListingCommercial,
        ListingContact,
        ListingIdentity,
        ListingKeyPerson,
        ListingProduct,
    )

    identity_data = data.get("identity", {})
    company_name = identity_data.get("company_name", "")
    if not company_name:
        return None

    listing = BusinessListing.objects.create(
        owner=None,
        source=BusinessListing.Source.EXCEL_IMPORT,
        status=BusinessListing.Status.DRAFT,
        last_modified_by=actor,
    )

    slug = generate_unique_slug(company_name)
    ListingIdentity.objects.create(listing=listing, slug=slug, **identity_data)

    contact_data = data.get("contact", {})
    if contact_data:
        ListingContact.objects.create(listing=listing, **contact_data)

    commercial_data = data.get("commercial", {})
    if any(commercial_data.values()):
        ListingCommercial.objects.create(listing=listing, **commercial_data)

    products = data.get("products", [])
    if products:
        ListingProduct.objects.bulk_create([
            ListingProduct(listing=listing, **p) for p in products if p.get("name")
        ])

    key_people = data.get("key_people", [])
    if key_people:
        from apps.listings.models import ListingKeyPerson
        ListingKeyPerson.objects.bulk_create([
            ListingKeyPerson(listing=listing, **kp) for kp in key_people if kp.get("full_name")
        ])

    return listing


class SampleImportFileView(APIView):
    permission_classes = [IsAdmin]

    def get(self, _request):
        file_path = os.path.join(settings.MEDIA_ROOT, "samples", "listings_import_sample.xlsx")
        if not os.path.exists(file_path):
            raise Http404("Sample file not found.")
        return FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename="listings_import_sample.xlsx",
        )
