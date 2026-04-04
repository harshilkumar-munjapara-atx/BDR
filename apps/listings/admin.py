from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    BusinessListing,
    ListingCommercial,
    ListingContact,
    ListingIdentity,
    ListingKeyPerson,
    ListingOffice,
    ListingProduct,
)


class ListingIdentityInline(admin.StackedInline):
    model = ListingIdentity
    extra = 0


class ListingContactInline(admin.StackedInline):
    model = ListingContact
    extra = 0


class ListingCommercialInline(admin.StackedInline):
    model = ListingCommercial
    extra = 0


class ListingOfficeInline(TabularInline):
    model = ListingOffice
    extra = 0


class ListingProductInline(TabularInline):
    model = ListingProduct
    extra = 0


class ListingKeyPersonInline(TabularInline):
    model = ListingKeyPerson
    extra = 0


@admin.register(BusinessListing)
class BusinessListingAdmin(ModelAdmin):
    list_display = ["get_company_name", "owner", "status", "source", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["identity__company_name", "owner__email"]
    readonly_fields = ["id", "created_at", "updated_at", "published_at"]
    inlines = [
        ListingIdentityInline,
        ListingContactInline,
        ListingCommercialInline,
        ListingOfficeInline,
        ListingProductInline,
        ListingKeyPersonInline,
    ]

    @admin.display(description="Company")
    def get_company_name(self, obj):
        try:
            return obj.identity.company_name
        except ListingIdentity.DoesNotExist:
            return "—"
