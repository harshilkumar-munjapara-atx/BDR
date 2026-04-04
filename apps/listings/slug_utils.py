from slugify import slugify

from .models import ListingIdentity


def generate_unique_slug(company_name: str, existing_id=None) -> str:
    base = slugify(company_name, max_length=255)
    slug = base
    counter = 1
    qs = ListingIdentity.objects.filter(slug=slug)
    if existing_id:
        qs = qs.exclude(listing_id=existing_id)
    while qs.exists():
        slug = f"{base}-{counter}"
        counter += 1
        qs = ListingIdentity.objects.filter(slug=slug)
        if existing_id:
            qs = qs.exclude(listing_id=existing_id)
    return slug
