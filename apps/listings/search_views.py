import hashlib
import json

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.cache import cache
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .models import BusinessListing
from .serializers import SearchResultSerializer


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        cache_key = "search:" + hashlib.md5(json.dumps(dict(params), sort_keys=True).encode()).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        base_qs = BusinessListing.objects.filter(
            status=BusinessListing.Status.PUBLISHED,
            is_deleted=False,
        ).select_related("identity", "contact", "commercial")

        # Facet filters (applied before text search so cascade respects them)
        sector = params.get("sector")
        if sector:
            base_qs = base_qs.filter(identity__sector_tags__contains=[sector])

        country = params.get("country")
        if country:
            base_qs = base_qs.filter(contact__hq_country__iexact=country)

        region = params.get("region")
        if region:
            base_qs = base_qs.filter(contact__regions_served__contains=[region])

        funding_stage = params.get("funding_stage")
        if funding_stage:
            base_qs = base_qs.filter(commercial__funding_stage__iexact=funding_stage)

        revenue_range = params.get("revenue_range")
        if revenue_range:
            base_qs = base_qs.filter(commercial__revenue_range__iexact=revenue_range)

        headcount = params.get("headcount")
        if headcount:
            base_qs = base_qs.filter(identity__headcount_range__iexact=headcount)

        company_type = params.get("company_type")
        if company_type:
            base_qs = base_qs.filter(identity__company_type__iexact=company_type)

        q = params.get("q", "").strip()
        if q:
            search_vector = (
                SearchVector("identity__company_name", weight="A")
                + SearchVector("identity__tagline", weight="A")
                + SearchVector("identity__description", weight="B")
                + SearchVector("products__name", weight="B")
                + SearchVector("key_people__full_name", weight="B")
                + SearchVector("products__short_description", weight="C")
                + SearchVector("contact__hq_country", weight="C")
                + SearchVector("contact__hq_city", weight="C")
                + SearchVector("commercial__funding_stage", weight="C")
                + SearchVector("commercial__revenue_range", weight="C")
            )
            search_query = SearchQuery(q, search_type="websearch")
            annotated_qs = base_qs.annotate(
                rank=SearchRank(search_vector, search_query),
                trigram=TrigramSimilarity("identity__company_name", q),
            )
            qs, match_type = self._run_tier_cascade(base_qs, annotated_qs, q)
        else:
            sort = params.get("sort", "newest")
            if sort == "name":
                qs = base_qs.order_by("identity__company_name")
            else:
                qs = base_qs.order_by("-published_at")
            match_type = None

        # Pagination
        page_size = 20
        try:
            page = max(1, int(params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        offset = (page - 1) * page_size
        total = qs.distinct().count()
        page_qs = qs.distinct()[offset: offset + page_size]

        data = {
            "count": total,
            "page": page,
            "page_size": page_size,
            "match_type": match_type,
            "results": SearchResultSerializer(
                list(page_qs.prefetch_related("products", "key_people")),
                many=True,
            ).data,
        }
        cache.set(cache_key, data, timeout=getattr(settings, "SEARCH_CACHE_TTL", 300))
        return Response(data)

    def _run_tier_cascade(self, base_qs, annotated_qs, q):
        # Tier 1: full-text + trigram, strict thresholds
        tier1 = annotated_qs.filter(
            Q(rank__gt=0.01) | Q(trigram__gt=0.1)
        ).order_by("-rank", "-trigram")
        if tier1.exists():
            return tier1, "exact"

        # Tier 2: same annotation, relaxed thresholds
        tier2 = annotated_qs.filter(
            Q(rank__gt=0) | Q(trigram__gt=0.05)
        ).order_by("-rank", "-trigram")
        if tier2.exists():
            return tier2, "fuzzy"

        # Tier 3: icontains across all text fields (no ArrayFields)
        tier3 = base_qs.filter(
            Q(identity__company_name__icontains=q)
            | Q(identity__tagline__icontains=q)
            | Q(identity__description__icontains=q)
            | Q(products__name__icontains=q)
            | Q(products__short_description__icontains=q)
            | Q(key_people__full_name__icontains=q)
            | Q(contact__hq_country__icontains=q)
            | Q(contact__hq_city__icontains=q)
            | Q(commercial__funding_stage__icontains=q)
            | Q(commercial__revenue_range__icontains=q)
        ).order_by("-published_at")
        if tier3.exists():
            return tier3, "partial"

        # Tier 4: per-token icontains across key fields
        tokens = [t for t in q.split() if len(t) >= 2]
        if tokens:
            token_filter = Q()
            for token in tokens:
                token_filter |= (
                    Q(identity__company_name__icontains=token)
                    | Q(identity__tagline__icontains=token)
                    | Q(products__name__icontains=token)
                    | Q(key_people__full_name__icontains=token)
                    | Q(contact__hq_country__icontains=token)
                )
            tier4 = base_qs.filter(token_filter).order_by("-published_at")
            if tier4.exists():
                return tier4, "token"

        # Tier 5: return all published listings
        return base_qs.order_by("-published_at"), "all"
