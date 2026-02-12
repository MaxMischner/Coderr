"""Offer views."""

from decimal import Decimal, InvalidOperation

from django.db.models import Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOfferOwner
from common.utils import (
    _apply_ordering,
    _get_authenticated_user,
    _get_business_profile_or_response,
    _get_ordering_param,
    _paginated_response,
)
from offers.models import Offer, OfferDetail
from offers.api.serializers import (
    OfferCreateSerializer,
    OfferDetailSerializer,
    OfferDetailViewSerializer,
    OfferListSerializer,
    OfferUpdateSerializer,
)


def _offers_base_queryset():
    """Return base offer queryset with prefetching."""
    queryset = Offer.objects.all().prefetch_related("details")
    return queryset.order_by("id")


def _annotate_offer_queryset(queryset):
    """Annotate offer queryset with computed fields."""
    return queryset.annotate(
        min_price=Min("details__price"),
        min_delivery_time=Min("details__delivery_time_in_days"),
    )


def _filter_offers_by_creator(queryset, request):
    """Filter offers by creator id query param."""
    creator_id = request.query_params.get("creator_id")
    if creator_id not in (None, ""):
        return queryset.filter(user_id=creator_id)
    return queryset


def _filter_offers_by_min_price(queryset, request):
    """Filter offers by minimum price param."""
    min_price = request.query_params.get("min_price")
    if min_price not in (None, ""):
        return queryset.filter(min_price__gte=min_price)
    return queryset


def _filter_offers_by_max_delivery(queryset, request):
    """Filter offers by maximum delivery time param."""
    max_delivery_time = request.query_params.get("max_delivery_time")
    if max_delivery_time not in (None, ""):
        return queryset.filter(min_delivery_time__lte=max_delivery_time)
    return queryset


def _filter_offers_by_search(queryset, request):
    """Filter offers by search term."""
    search = request.query_params.get("search")
    if search:
        return queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
    return queryset


def _apply_offers_filters(queryset, request):
    """Apply all offer filters from query params."""
    queryset = _filter_offers_by_creator(queryset, request)
    queryset = _filter_offers_by_min_price(queryset, request)
    queryset = _filter_offers_by_max_delivery(queryset, request)
    return _filter_offers_by_search(queryset, request)


def _validate_offer_filters(request):
    """Validate filter query params and return a response for bad input."""
    creator_id = request.query_params.get("creator_id")
    if creator_id not in (None, ""):
        try:
            int(creator_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "creator_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    min_price = request.query_params.get("min_price")
    if min_price not in (None, ""):
        try:
            Decimal(min_price)
        except (TypeError, ValueError, InvalidOperation):
            return Response(
                {"detail": "min_price must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    max_delivery_time = request.query_params.get("max_delivery_time")
    if max_delivery_time not in (None, ""):
        try:
            int(max_delivery_time)
        except (TypeError, ValueError):
            return Response(
                {"detail": "max_delivery_time must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    return None


def _create_offer_from_request(request):
    """Create an offer from request payload."""
    serializer = OfferCreateSerializer(
        data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def _get_authenticated_user_or_response(request):
    """Return authenticated user or a 401 response."""
    user = _get_authenticated_user(request)
    if not user:
        return None, Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return user, None


class OffersListCreateView(APIView):
    """List offers or create a new offer."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        allowed = {"updated_at", "-updated_at", "min_price", "-min_price"}
        ordering, is_valid = _get_ordering_param(request, allowed)
        if not is_valid:
            return Response(
                {"detail": "Invalid ordering parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = _validate_offer_filters(request)
        if response:
            return response
        queryset = _offers_base_queryset()
        queryset = _annotate_offer_queryset(queryset)
        queryset = _apply_offers_filters(queryset, request)
        queryset = _apply_ordering(queryset, ordering)
        return _paginated_response(request, queryset, OfferListSerializer)

    def post(self, request):
        user, response = _get_authenticated_user_or_response(request)
        if response:
            return response
        _, response = _get_business_profile_or_response(user)
        if response:
            return response
        offer = _create_offer_from_request(request)
        response_serializer = OfferCreateSerializer(
            offer, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OfferDetailUpdateDeleteView(APIView):
    """Retrieve, update, or delete an offer."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        _, response = _get_authenticated_user_or_response(request)
        if response:
            return response
        offer = get_object_or_404(Offer, pk=pk)
        serializer = OfferDetailViewSerializer(
            offer, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        _, response = _get_authenticated_user_or_response(request)
        if response:
            return response
        offer = get_object_or_404(Offer, pk=pk)
        if not IsOfferOwner().has_object_permission(request, self, offer):
            return Response(
                {"detail": "You do not have permission to modify this offer."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OfferUpdateSerializer(
            offer, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = OfferCreateSerializer(
            offer, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        _, response = _get_authenticated_user_or_response(request)
        if response:
            return response
        offer = get_object_or_404(Offer, pk=pk)
        if not IsOfferOwner().has_object_permission(request, self, offer):
            return Response(
                {"detail": "You do not have permission to delete this offer."},
                status=status.HTTP_403_FORBIDDEN,
            )
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailRetrieveView(APIView):
    """Retrieve a single offer detail record."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        _, response = _get_authenticated_user_or_response(request)
        if response:
            return response
        detail = get_object_or_404(OfferDetail, pk=pk)
        serializer = OfferDetailSerializer(detail)
        return Response(serializer.data)
