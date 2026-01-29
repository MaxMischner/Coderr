"""API views for Coderr backend."""

from django.contrib.auth import get_user_model
from django.db.models import Avg, Min, Q
from django.shortcuts import get_object_or_404
from rest_framework import pagination, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Offer, OfferDetail, Order, Profile, Review
from .permissions import (
    IsCustomerUser,
    IsOfferOwner,
    IsOrderBusinessOwner,
    IsProfileOwner,
    IsReviewOwner,
    IsStaffUser,
)
from .serializers import (
    BaseInfoSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    LoginSerializer,
    OfferCreateSerializer,
    OfferDetailSerializer,
    OfferDetailViewSerializer,
    OfferListSerializer,
    OfferUpdateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
    ProfileSerializer,
    RegistrationSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)


User = get_user_model()


def _get_ordering_param(request, allowed):
    """Return ordering param and validity flag."""
    ordering = request.query_params.get("ordering")
    if ordering and ordering not in allowed:
        return ordering, False
    return ordering, True


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


def _apply_ordering(queryset, ordering):
    """Apply ordering when provided."""
    if ordering:
        return queryset.order_by(ordering)
    return queryset


def _paginated_response(request, queryset, serializer_cls):
    """Return a paginated response for a queryset."""
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_cls(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def _get_authenticated_user(request):
    """Return authenticated user or None."""
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user
    return None


def _get_business_profile_or_response(user):
    """Return business profile or a forbidden response."""
    profile = _get_or_create_profile(user, default_type=Profile.TYPE_BUSINESS)
    if profile.type != Profile.TYPE_BUSINESS:
        return None, Response(status=status.HTTP_403_FORBIDDEN)
    return profile, None


def _create_offer_from_request(request):
    """Create an offer from request payload."""
    serializer = OfferCreateSerializer(
        data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def _orders_for_user(user):
    """Return orders where user is customer or business."""
    return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))


def _get_offer_detail_or_response(request):
    """Return offer detail or a bad request response."""
    if "offer_detail_id" not in request.data:
        return None, Response(status=status.HTTP_400_BAD_REQUEST)
    offer_detail = get_object_or_404(
        OfferDetail, pk=request.data.get("offer_detail_id"))
    return offer_detail, None


def _create_order_from_detail(customer_user, offer_detail):
    """Create an order for a given offer detail."""
    return Order.objects.create(
        customer_user=customer_user,
        business_user=offer_detail.offer.user,
        title=offer_detail.title,
        revisions=offer_detail.revisions,
        delivery_time_in_days=offer_detail.delivery_time_in_days,
        price=offer_detail.price,
        features=offer_detail.features,
        offer_type=offer_detail.offer_type,
    )


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


def _guess_profile_type(user):
    """Infer profile type from user identity hints."""
    username = (user.username or "").lower()
    email = (user.email or "").lower()
    if "customer" in username or "customer" in email:
        return Profile.TYPE_CUSTOMER
    if "business" in username or "business" in email or username.startswith("biz") or "biz" in username:
        return Profile.TYPE_BUSINESS
    return None


def _get_or_create_profile(user, default_type=None):
    """Return existing profile or create with default type."""
    try:
        return user.profile
    except Profile.DoesNotExist:
        inferred_type = _guess_profile_type(user)
        profile_type = inferred_type or default_type or Profile.TYPE_CUSTOMER
        return Profile.objects.create(user=user, type=profile_type)


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Pagination settings for list endpoints."""
    page_size = 6
    page_size_query_param = "page_size"


class ProfileDetailView(APIView):
    """Retrieve and update profile details."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile = _get_or_create_profile(user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile = _get_or_create_profile(user)
        if not IsProfileOwner().has_object_permission(request, self, profile):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ProfileSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BusinessProfilesListView(APIView):
    """List business profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = Profile.objects.filter(type=Profile.TYPE_BUSINESS)
        serializer = BusinessProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class CustomerProfilesListView(APIView):
    """List customer profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = Profile.objects.filter(type=Profile.TYPE_CUSTOMER)
        serializer = CustomerProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class OffersListCreateView(APIView):
    """List offers or create a new offer."""
    def get(self, request):
        allowed = {"updated_at", "-updated_at", "min_price", "-min_price"}
        ordering, is_valid = _get_ordering_param(request, allowed)
        if not is_valid:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        queryset = _offers_base_queryset()
        queryset = _annotate_offer_queryset(queryset)
        queryset = _apply_offers_filters(queryset, request)
        queryset = _apply_ordering(queryset, ordering)
        return _paginated_response(request, queryset, OfferListSerializer)

    def post(self, request):
        user = _get_authenticated_user(request)
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
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
        offer = get_object_or_404(Offer, pk=pk)
        serializer = OfferDetailViewSerializer(
            offer, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)
        if not IsOfferOwner().has_object_permission(request, self, offer):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = OfferUpdateSerializer(
            offer, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = OfferCreateSerializer(
            offer, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)
        if not IsOfferOwner().has_object_permission(request, self, offer):
            return Response(status=status.HTTP_403_FORBIDDEN)
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailRetrieveView(APIView):
    """Retrieve a single offer detail record."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        detail = get_object_or_404(OfferDetail, pk=pk)
        serializer = OfferDetailSerializer(detail)
        return Response(serializer.data)


class OrdersListCreateView(APIView):
    """List orders or create a new order."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = _orders_for_user(request.user)
        return Response(OrderSerializer(queryset, many=True).data)

    def post(self, request):
        if not IsCustomerUser().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        offer_detail, response = _get_offer_detail_or_response(request)
        if response:
            return response
        order = _create_order_from_detail(request.user, offer_detail)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrdersUpdateDeleteView(APIView):
    """Update or delete orders."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not IsOrderBusinessOwner().has_object_permission(request, self, order):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = OrderStatusUpdateSerializer(
            order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    def delete(self, request, pk):
        if not IsStaffUser().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderCountView(APIView):
    """Return count of in-progress orders for a business user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id):
        user = get_object_or_404(User, pk=business_user_id)
        profile = _get_or_create_profile(user)
        if profile.type != Profile.TYPE_BUSINESS:
            return Response(status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(
            business_user_id=business_user_id, status=Order.STATUS_IN_PROGRESS
        ).count()
        return Response({"order_count": count})


class CompletedOrderCountView(APIView):
    """Return count of completed orders for a business user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id):
        user = get_object_or_404(User, pk=business_user_id)
        profile = _get_or_create_profile(user)
        if profile.type != Profile.TYPE_BUSINESS:
            return Response(status=status.HTTP_404_NOT_FOUND)
        count = Order.objects.filter(
            business_user_id=business_user_id, status=Order.STATUS_COMPLETED
        ).count()
        return Response({"completed_order_count": count})


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


class RegistrationView(APIView):
    """Register a new user and return token."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return token."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


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
