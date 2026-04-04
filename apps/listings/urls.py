from django.urls import path

from .email_verification_views import ConfirmContactEmailVerificationView, SendContactEmailVerificationView
from .search_views import SearchView
from .views import ListingPublicDetailView, MyListingSubmitView, MyListingView

urlpatterns = [
    path("listings/mine/", MyListingView.as_view(), name="my-listing"),
    path("listings/mine/submit/", MyListingSubmitView.as_view(), name="my-listing-submit"),
    path("listings/mine/send-verification/", SendContactEmailVerificationView.as_view(), name="my-listing-send-verification"),
    path("listings/mine/verify-email/", ConfirmContactEmailVerificationView.as_view(), name="my-listing-verify-email"),
    path("listings/<slug:slug>/", ListingPublicDetailView.as_view(), name="listing-detail"),
    path("search/", SearchView.as_view(), name="search"),
]
