import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.accounts.models import User
from apps.listings.models import (
    BusinessListing,
    ListingCommercial,
    ListingContact,
    ListingIdentity,
    ListingKeyPerson,
    ListingOffice,
    ListingProduct,
)

COMPANY_NAMES = [
    "Apex Dynamics", "BlueWave Solutions", "ClearPath Technologies", "DeltaForge",
    "EchoStream", "FusionBridge", "GridNova", "HorizonEdge", "InfraCore",
    "JetLink Systems", "Kinetic Labs", "LuminaTech", "MeshPoint", "NexaCloud",
    "Orbital Analytics", "PinnacleSoft", "QuantumLeap", "ReefData", "Solaris AI",
    "TrueNorth Digital", "Unified Networks", "VantageOps", "WaveSync", "Xplore Capital",
    "YieldBridge", "ZenithStack", "Arrowhead Ventures", "Beacon Analytics",
    "Cascade Systems", "Drift Technologies", "Ember Platforms", "FlowState",
    "GreenMark Solutions", "HarbourTech", "Ironclad Software", "Juno Networks",
    "Kaleidoscope AI", "Lattice Cloud", "Moxie Systems", "Numen Labs",
    "Overture Capital", "Parallax Data", "Quickset Technologies", "Radius Finance",
    "Sentinel Group", "Titan Platforms", "Uplift Digital", "Vertex Analytics",
    "Windfall Networks", "Xenon AI",
]

TAGLINES = [
    "Powering the future of business",
    "Data-driven decisions, simplified",
    "Where innovation meets execution",
    "Connecting ideas to outcomes",
    "Building tomorrow's infrastructure today",
    "Smarter software for smarter teams",
    "Your growth, our mission",
    "Transforming industries through technology",
    "Scale without limits",
    "Insight at the speed of business",
]

DESCRIPTIONS = [
    "A leading provider of enterprise software solutions focused on streamlining operations and driving measurable growth for mid-market companies.",
    "We build cloud-native platforms that help businesses automate workflows, reduce operational costs, and unlock new revenue streams.",
    "Specializing in AI-powered analytics tools that turn raw data into actionable intelligence for finance, logistics, and retail sectors.",
    "Our mission is to bridge the gap between complex technology and everyday business needs through intuitive, scalable software products.",
    "Founded by industry veterans, we deliver cutting-edge cybersecurity and compliance solutions to regulated industries worldwide.",
    "A B2B SaaS company helping operations teams eliminate manual work and scale their processes with intelligent automation.",
    "We partner with growth-stage companies to build resilient digital infrastructure that supports rapid expansion across global markets.",
    "Our platform connects buyers and sellers in emerging markets, reducing friction and enabling faster, more transparent transactions.",
]

SECTORS = [
    ["FinTech", "SaaS"], ["HealthTech", "AI"], ["EdTech", "B2B"],
    ["Logistics", "Supply Chain"], ["Cybersecurity", "Cloud"],
    ["E-commerce", "Marketplace"], ["PropTech", "Real Estate"],
    ["CleanTech", "Energy"], ["AdTech", "Media"], ["HRTech", "Workforce"],
]

HEADCOUNTS = ["1-10", "11-50", "51-200", "201-500", "500+"]
REVENUE_RANGES = ["<$1M", "$1M-$5M", "$5M-$20M", "$20M-$50M", "$50M+"]
FUNDING_STAGES = ["Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Bootstrapped"]
BUSINESS_TYPES = [
    ["B2B", "SaaS"], ["B2C", "Marketplace"], ["B2B2C", "Platform"],
    ["Enterprise", "SaaS"], ["SME", "Services"],
]

COUNTRIES = ["Nigeria", "Kenya", "Ghana", "South Africa", "Egypt", "Ethiopia", "Rwanda", "Senegal"]
CITIES = {
    "Nigeria": ["Lagos", "Abuja", "Port Harcourt"],
    "Kenya": ["Nairobi", "Mombasa"],
    "Ghana": ["Accra", "Kumasi"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban"],
    "Egypt": ["Cairo", "Alexandria"],
    "Ethiopia": ["Addis Ababa"],
    "Rwanda": ["Kigali"],
    "Senegal": ["Dakar"],
}
TIMEZONES = ["Africa/Lagos", "Africa/Nairobi", "Africa/Accra", "Africa/Johannesburg", "Africa/Cairo"]
REGIONS = ["West Africa", "East Africa", "Southern Africa", "North Africa", "Pan-Africa"]

PRODUCT_NAMES = [
    "Core Platform", "Analytics Suite", "Connect API", "AutoFlow", "DataBridge",
    "InsightHub", "SecureVault", "TeamPortal", "ReportBuilder", "PayEngine",
]
PRODUCT_CATEGORIES = ["SaaS", "API", "Mobile App", "Desktop App", "Integration", "Data Tool"]

FIRST_NAMES = ["Amara", "Chidi", "Fatima", "Kwame", "Ngozi", "Seun", "Tunde", "Yemi", "Ade", "Bola"]
LAST_NAMES = ["Okafor", "Mensah", "Ibrahim", "Diallo", "Kamara", "Banda", "Mwangi", "Nkosi", "Toure", "Eze"]
JOB_TITLES = ["CEO", "CTO", "COO", "CFO", "Head of Product", "VP Engineering", "MD", "Founder"]

STATUSES = [
    BusinessListing.Status.PUBLISHED,
    BusinessListing.Status.PUBLISHED,
    BusinessListing.Status.PUBLISHED,
    BusinessListing.Status.PENDING,
    BusinessListing.Status.DRAFT,
]


def _unique_slug(base_slug):
    slug = slugify(base_slug)
    candidate = slug
    counter = 1
    while ListingIdentity.objects.filter(slug=candidate).exists():
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


class Command(BaseCommand):
    help = "Seed 50 dummy BusinessListings for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of listings to create (default: 50)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing seed listings before creating new ones",
        )

    def handle(self, *args, **options):
        count = options["count"]

        if options["clear"]:
            deleted, _ = BusinessListing.objects.filter(source=BusinessListing.Source.MANUAL, owner=None).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing ownerless listings."))

        created = 0
        for i in range(count):
            company_name = COMPANY_NAMES[i % len(COMPANY_NAMES)]
            # Append index to avoid duplicates if seeding multiple times
            unique_name = f"{company_name} {i + 1}" if ListingIdentity.objects.filter(company_name=company_name).exists() else company_name

            country = random.choice(COUNTRIES)
            city = random.choice(CITIES[country])
            status = random.choice(STATUSES)

            listing = BusinessListing.objects.create(
                status=status,
                source=BusinessListing.Source.MANUAL,
                owner=None,
            )

            ListingIdentity.objects.create(
                listing=listing,
                company_name=unique_name,
                slug=_unique_slug(unique_name),
                tagline=random.choice(TAGLINES),
                description=random.choice(DESCRIPTIONS),
                company_type=random.choice([c[0] for c in ListingIdentity.CompanyType.choices]),
                sector_tags=random.choice(SECTORS),
                founded_year=random.randint(2005, 2023),
                headcount_range=random.choice(HEADCOUNTS),
                website_url=f"https://www.{slugify(unique_name)}.com",
                linkedin_url=f"https://linkedin.com/company/{slugify(unique_name)}",
            )

            ListingContact.objects.create(
                listing=listing,
                primary_email=f"contact@{slugify(unique_name)}.com",
                primary_phone=f"+234{random.randint(7000000000, 9099999999)}",
                hq_country=country,
                hq_city=city,
                regions_served=random.sample(REGIONS, k=random.randint(1, 3)),
                timezone=random.choice(TIMEZONES),
            )

            ListingCommercial.objects.create(
                listing=listing,
                revenue_range=random.choice(REVENUE_RANGES),
                funding_stage=random.choice(FUNDING_STAGES),
                business_type_tags=random.choice(BUSINESS_TYPES),
            )

            ListingOffice.objects.create(
                listing=listing,
                country=country,
                city=city,
                is_hq=True,
            )

            # 1-2 products per listing
            for j in range(random.randint(1, 2)):
                product_name = random.choice(PRODUCT_NAMES)
                ListingProduct.objects.create(
                    listing=listing,
                    name=product_name,
                    short_description=f"A powerful {product_name.lower()} for modern teams.",
                    category_tag=random.choice(PRODUCT_CATEGORIES),
                )

            # 1-2 key people per listing
            for k in range(random.randint(1, 2)):
                full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                ListingKeyPerson.objects.create(
                    listing=listing,
                    full_name=full_name,
                    job_title=random.choice(JOB_TITLES),
                    linkedin_url=f"https://linkedin.com/in/{slugify(full_name)}",
                    display_order=k,
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created} dummy listings."))
