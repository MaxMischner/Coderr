"""Base info view."""

from django.db.models import Avg
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from markt_coderr.models import Offer, Profile, Review


class BaseInfoView(APIView):
    """Return base info statistics."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        review_stats = Review.objects.aggregate(avg=Avg("rating"))
        avg = review_stats["avg"] or 0
        data = {
            "review_count": Review.objects.count(),
            "average_rating": round(avg, 1),
            "business_profile_count": Profile.objects.filter(type=Profile.TYPE_BUSINESS).count(),
            "offer_count": Offer.objects.count(),
        }
        return Response(data)
