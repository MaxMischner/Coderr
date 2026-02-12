"""Review views."""

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCustomerUser, IsReviewOwner
from common.utils import _apply_ordering, _get_ordering_param
from reviews.models import Review
from reviews.api.serializers import ReviewCreateSerializer, ReviewSerializer, ReviewUpdateSerializer


def _filter_reviews_by_business(queryset, request):
    """Filter reviews by business user id param."""
    business_user_id = request.query_params.get("business_user_id")
    if business_user_id:
        return queryset.filter(business_user_id=business_user_id)
    return queryset


def _filter_reviews_by_reviewer(queryset, request):
    """Filter reviews by reviewer id param."""
    reviewer_id = request.query_params.get("reviewer_id")
    if reviewer_id:
        return queryset.filter(reviewer_id=reviewer_id)
    return queryset


def _apply_reviews_filters(queryset, request):
    """Apply review filters from query params."""
    queryset = _filter_reviews_by_business(queryset, request)
    return _filter_reviews_by_reviewer(queryset, request)


class ReviewsListCreateView(APIView):
    """List reviews or create a review."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        allowed = {"updated_at", "-updated_at", "rating", "-rating"}
        ordering, is_valid = _get_ordering_param(request, allowed)
        if not is_valid:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        queryset = _apply_reviews_filters(Review.objects.all(), request)
        queryset = _apply_ordering(queryset, ordering)
        return Response(ReviewSerializer(queryset, many=True).data)

    def post(self, request):
        if not IsCustomerUser().has_permission(request, self):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = ReviewCreateSerializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        business_user_id = serializer.validated_data["business_user"].id
        if Review.objects.filter(business_user_id=business_user_id, reviewer=request.user).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewsUpdateDeleteView(APIView):
    """Update or delete a review."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if not IsReviewOwner().has_object_permission(request, self, review):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ReviewUpdateSerializer(
            review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReviewSerializer(review).data)

    def delete(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if not IsReviewOwner().has_object_permission(request, self, review):
            return Response(status=status.HTTP_403_FORBIDDEN)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
