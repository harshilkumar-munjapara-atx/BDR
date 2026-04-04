import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class BusinessListing(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending Review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        EXCEL_IMPORT = "excel_import", "Excel Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="listing",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    contact_email_verified = models.BooleanField(default=False)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_listings",
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_listings"

    def __str__(self):
        name = getattr(self, "_identity_name", None)
        return name or f"Listing {self.id}"


class ListingIdentity(models.Model):
    class CompanyType(models.TextChoices):
        STARTUP = "startup", "Startup"
        SME = "sme", "SME"
        ENTERPRISE = "enterprise", "Enterprise"
        NGO = "ngo", "NGO"
        OTHER = "other", "Other"

    listing = models.OneToOneField(BusinessListing, on_delete=models.CASCADE, related_name="identity")
    company_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    logo_url = models.URLField(blank=True)
    tagline = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    company_type = models.CharField(max_length=20, choices=CompanyType.choices, blank=True)
    sector_tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    founded_year = models.PositiveSmallIntegerField(null=True, blank=True)
    headcount_range = models.CharField(max_length=50, blank=True)
    website_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    other_social = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "listing_identity"

    def __str__(self):
        return self.company_name


class ListingContact(models.Model):
    listing = models.OneToOneField(BusinessListing, on_delete=models.CASCADE, related_name="contact")
    primary_email = models.EmailField()
    primary_phone = models.CharField(max_length=30, blank=True)
    hq_country = models.CharField(max_length=100, blank=True)
    hq_city = models.CharField(max_length=100, blank=True)
    regions_served = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    timezone = models.CharField(max_length=60, blank=True)

    class Meta:
        db_table = "listing_contact"


class ListingOffice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(BusinessListing, on_delete=models.CASCADE, related_name="offices")
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    is_hq = models.BooleanField(default=False)

    class Meta:
        db_table = "listing_offices"


class ListingCommercial(models.Model):
    listing = models.OneToOneField(BusinessListing, on_delete=models.CASCADE, related_name="commercial")
    revenue_range = models.CharField(max_length=50, blank=True)
    funding_stage = models.CharField(max_length=50, blank=True)
    business_type_tags = ArrayField(models.CharField(max_length=100), default=list, blank=True)

    class Meta:
        db_table = "listing_commercial"


class ListingProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(BusinessListing, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    category_tag = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "listing_products"


class ListingKeyPerson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(BusinessListing, on_delete=models.CASCADE, related_name="key_people")
    full_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "listing_key_people"
        ordering = ["display_order"]


class EmailVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(BusinessListing, on_delete=models.CASCADE, related_name="email_verifications")
    email_address = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "email_verifications"

    def __str__(self):
        return f"Verification for {self.email_address} ({self.listing_id})"
