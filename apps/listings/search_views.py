import hashlib
import json

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.cache import cache
from django.db.models import F, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .models import BusinessListing
from .serializers import AdminListingListSerializer


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        cache_key = "search:" + hashlib.md5(json.dumps(dict(params), sort_keys=True).encode()).hexdigest()
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        qs = BusinessListing.objects.filter(
            status=BusinessListing.Status.PUBLISHED,
            is_deleted=False,
        ).select_related("identity", "contact", "commercial")

        q = params.get("q", "").strip()
        if q:
            # Full-text search with trigram fallback
            search_vector = (
                SearchVector("identity__company_name", weight="A")
                + SearchVector("identity__tagline", weight="A")
                + SearchVector("identity__description", weight="B")
                + SearchVector("products__name", weight="B")
                + SearchVector("products__short_description", weight="C")
            )
            search_query = SearchQuery(q, search_type="websearch")
            qs = (
                qs.annotate(
                    rank=SearchRank(search_vector, search_query),
                    trigram=TrigramSimilarity("identity__company_name", q),
                )
                .filter(Q(rank__gt=0.01) | Q(trigram__gt=0.1))
                .order_by("-rank", "-trigram")
            )
        else:
            sort = params.get("sort", "newest")
            if sort == "name":
                qs = qs.order_by("identity__company_name")
            else:
                qs = qs.order_by("-published_at")

        # Filters
        sector = params.get("sector")
        if sector:
            qs = qs.filter(identity__sector_tags__contains=[sector])

        country = params.get("country")
        if country:
            qs = qs.filter(contact__hq_country__iexact=country)

        region = params.get("region")
        if region:
            qs = qs.filter(contact__regions_served__contains=[region])

        funding_stage = params.get("funding_stage")
        if funding_stage:
            qs = qs.filter(commercial__funding_stage__iexact=funding_stage)

        revenue_range = params.get("revenue_range")
        if revenue_range:
            qs = qs.filter(commercial__revenue_range__iexact=revenue_range)

        headcount = params.get("headcount")
        if headcount:
            qs = qs.filter(identity__headcount_range__iexact=headcount)

        company_type = params.get("company_type")
        if company_type:
            qs = qs.filter(identity__company_type__iexact=company_type)

        # Pagination
        page_size = 20
        try:
            page = max(1, int(params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        offset = (page - 1) * page_size
        total = qs.count()
        results = qs.distinct()[offset: offset + page_size]

        data = {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": AdminListingListSerializer(results, many=True).data,
        }
        cache.set(cache_key, data, timeout=getattr(settings, "SEARCH_CACHE_TTL", 300))
        return Response(data)
