from rest_framework import serializers

from .models import (
    BusinessListing,
    ListingCommercial,
    ListingContact,
    ListingIdentity,
    ListingKeyPerson,
    ListingOffice,
    ListingProduct,
)
from .slug_utils import generate_unique_slug


class ListingOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingOffice
        fields = ["id", "country", "city", "is_hq"]
        read_only_fields = ["id"]


class ListingProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingProduct
        fields = ["id", "name", "short_description", "category_tag"]
        read_only_fields = ["id"]


class ListingKeyPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingKeyPerson
        fields = ["id", "full_name", "job_title", "linkedin_url", "display_order"]
        read_only_fields = ["id"]


class ListingIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingIdentity
        exclude = ["listing", "slug"]


class ListingContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingContact
        exclude = ["listing"]


class ListingCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingCommercial
        exclude = ["listing"]


class ListingDetailSerializer(serializers.ModelSerializer):
    identity = ListingIdentitySerializer()
    contact = ListingContactSerializer()
    commercial = ListingCommercialSerializer()
    offices = ListingOfficeSerializer(many=True)
    products = ListingProductSerializer(many=True)
    key_people = ListingKeyPersonSerializer(many=True)
    slug = serializers.CharField(source="identity.slug", read_only=True)

    class Meta:
        model = BusinessListing
        fields = [
            "id", "slug", "status", "source", "contact_email_verified",
            "published_at", "created_at", "updated_at",
            "identity", "contact", "commercial", "offices", "products", "key_people",
        ]
        read_only_fields = ["id", "status", "source", "published_at", "created_at", "updated_at", "slug"]


class ListingWriteSerializer(serializers.ModelSerializer):
    identity = ListingIdentitySerializer()
    contact = ListingContactSerializer()
    commercial = ListingCommercialSerializer(required=False)
    offices = ListingOfficeSerializer(many=True, required=False)
    products = ListingProductSerializer(many=True, required=False)
    key_people = ListingKeyPersonSerializer(many=True, required=False)

    class Meta:
        model = BusinessListing
        fields = ["identity", "contact", "commercial", "offices", "products", "key_people"]

    def _save_nested(self, listing, validated_data):
        identity_data = validated_data.pop("identity", None)
        contact_data = validated_data.pop("contact", None)
        commercial_data = validated_data.pop("commercial", None)
        # Use None as sentinel so we can distinguish "not sent" from "sent as []"
        offices_data = validated_data.pop("offices", None)
        products_data = validated_data.pop("products", None)
        key_people_data = validated_data.pop("key_people", None)

        if identity_data is not None:
            # company_name may be absent in a partial update — fall back to existing
            company_name = identity_data.get("company_name") or getattr(
                getattr(listing, "identity", None), "company_name", ""
            )
            slug = generate_unique_slug(company_name, existing_id=listing.pk)
            ListingIdentity.objects.update_or_create(
                listing=listing,
                defaults={**identity_data, "slug": slug},
            )

        if contact_data is not None:
            ListingContact.objects.update_or_create(listing=listing, defaults=contact_data)

        if commercial_data is not None:
            ListingCommercial.objects.update_or_create(listing=listing, defaults=commercial_data)

        if offices_data is not None:
            listing.offices.all().delete()
            ListingOffice.objects.bulk_create([
                ListingOffice(listing=listing, **o) for o in offices_data
            ])

        if products_data is not None:
            listing.products.all().delete()
            ListingProduct.objects.bulk_create([
                ListingProduct(listing=listing, **p) for p in products_data
            ])

        if key_people_data is not None:
            listing.key_people.all().delete()
            ListingKeyPerson.objects.bulk_create([
                ListingKeyPerson(listing=listing, **kp) for kp in key_people_data
            ])

    def create(self, validated_data):
        listing = BusinessListing.objects.create(
            owner=self.context["request"].user,
            last_modified_by=self.context["request"].user,
        )
        self._save_nested(listing, validated_data)
        return listing

    def update(self, instance, validated_data):
        instance.last_modified_by = self.context["request"].user
        # If published, revert to pending on edit
        if instance.status == BusinessListing.Status.PUBLISHED:
            instance.status = BusinessListing.Status.PENDING
            instance.published_at = None
        instance.save()
        self._save_nested(instance, validated_data)
        return instance


class ListingSubmitSerializer(serializers.ModelSerializer):
    """Moves a draft listing to pending (submit for review)."""
    class Meta:
        model = BusinessListing
        fields = ["status"]
        read_only_fields = ["status"]

    def validate(self, attrs):
        listing = self.instance
        if listing.status not in [BusinessListing.Status.DRAFT]:
            raise serializers.ValidationError("Only draft listings can be submitted.")
        if not hasattr(listing, "identity"):
            raise serializers.ValidationError("Listing must have identity information before submitting.")
        if not hasattr(listing, "contact"):
            raise serializers.ValidationError("Listing must have contact information before submitting.")
        return attrs

    def update(self, instance, validated_data):
        instance.status = BusinessListing.Status.PENDING
        instance.save()
        return instance


# --- Admin serializers ---

class AdminListingListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="identity.company_name", default="")
    slug = serializers.CharField(source="identity.slug", default="")
    owner_email = serializers.EmailField(source="owner.email", default="")

    class Meta:
        model = BusinessListing
        fields = ["id", "company_name", "slug", "owner_email", "status", "source", "created_at", "updated_at"]


class SearchResultSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="identity.company_name", default="")
    slug = serializers.CharField(source="identity.slug", default="")
    tagline = serializers.CharField(source="identity.tagline", default="")
    logo_url = serializers.URLField(source="identity.logo_url", default="")
    sector_tags = serializers.ListField(
        child=serializers.CharField(), source="identity.sector_tags", default=list
    )
    hq_country = serializers.CharField(source="contact.hq_country", default="")
    hq_city = serializers.CharField(source="contact.hq_city", default="")
    funding_stage = serializers.CharField(source="commercial.funding_stage", default="")
    products = ListingProductSerializer(many=True, read_only=True)
    key_people = ListingKeyPersonSerializer(many=True, read_only=True)

    class Meta:
        model = BusinessListing
        fields = [
            "id", "slug", "company_name", "tagline", "logo_url",
            "sector_tags", "hq_country", "hq_city", "funding_stage",
            "products", "key_people",
            "status", "source", "published_at", "created_at", "updated_at",
        ]


class AdminPublishSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessListing
        fields = ["status", "published_at"]
        read_only_fields = ["published_at"]

    def update(self, instance, validated_data):
        from django.utils import timezone
        target = validated_data.get("status")
        if target == BusinessListing.Status.PUBLISHED:
            instance.status = BusinessListing.Status.PUBLISHED
            instance.published_at = timezone.now()
        elif target == BusinessListing.Status.DRAFT:
            instance.status = BusinessListing.Status.DRAFT
            instance.published_at = None
        instance.save()
        return instance
