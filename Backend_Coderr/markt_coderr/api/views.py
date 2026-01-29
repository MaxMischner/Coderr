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


def _guess_profile_type(user):
	username = (user.username or "").lower()
	email = (user.email or "").lower()
	if "customer" in username or "customer" in email:
		return Profile.TYPE_CUSTOMER
	if "business" in username or "business" in email or username.startswith("biz") or "biz" in username:
		return Profile.TYPE_BUSINESS
	return None


def _get_or_create_profile(user, default_type=None):
	try:
		return user.profile
	except Profile.DoesNotExist:
		inferred_type = _guess_profile_type(user)
		profile_type = inferred_type or default_type or Profile.TYPE_CUSTOMER
		return Profile.objects.create(user=user, type=profile_type)


class StandardResultsSetPagination(pagination.PageNumberPagination):
	page_size = 6
	page_size_query_param = "page_size"


class ProfileDetailView(APIView):
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
		serializer = ProfileSerializer(profile, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)


class BusinessProfilesListView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		profiles = Profile.objects.filter(type=Profile.TYPE_BUSINESS)
		serializer = BusinessProfileListSerializer(profiles, many=True)
		return Response(serializer.data)


class CustomerProfilesListView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		profiles = Profile.objects.filter(type=Profile.TYPE_CUSTOMER)
		serializer = CustomerProfileListSerializer(profiles, many=True)
		return Response(serializer.data)


class OffersListCreateView(APIView):
	def get(self, request):
		ordering = request.query_params.get("ordering")
		allowed_ordering = {"updated_at", "-updated_at", "min_price", "-min_price"}
		if ordering and ordering not in allowed_ordering:
			return Response(status=status.HTTP_400_BAD_REQUEST)

		queryset = Offer.objects.all().prefetch_related("details")
		queryset = queryset.order_by("id")
		queryset = queryset.annotate(
			min_price=Min("details__price"),
			min_delivery_time=Min("details__delivery_time_in_days"),
		)

		creator_id = request.query_params.get("creator_id")
		if creator_id not in (None, ""):
			queryset = queryset.filter(user_id=creator_id)
		min_price = request.query_params.get("min_price")
		if min_price not in (None, ""):
			queryset = queryset.filter(min_price__gte=min_price)
		max_delivery_time = request.query_params.get("max_delivery_time")
		if max_delivery_time not in (None, ""):
			queryset = queryset.filter(min_delivery_time__lte=max_delivery_time)
		search = request.query_params.get("search")
		if search:
			queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

		if ordering:
			queryset = queryset.order_by(ordering)

		paginator = StandardResultsSetPagination()
		page = paginator.paginate_queryset(queryset, request)
		serializer = OfferListSerializer(page, many=True, context={"request": request})
		return paginator.get_paginated_response(serializer.data)

	def post(self, request):
		if not request.user or not request.user.is_authenticated:
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		profile = _get_or_create_profile(request.user, default_type=Profile.TYPE_BUSINESS)
		if profile.type != Profile.TYPE_BUSINESS:
			return Response(status=status.HTTP_403_FORBIDDEN)
		serializer = OfferCreateSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		offer = serializer.save()
		response_serializer = OfferCreateSerializer(offer, context={"request": request})
		return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OfferDetailUpdateDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, pk):
		offer = get_object_or_404(Offer, pk=pk)
		serializer = OfferDetailViewSerializer(offer, context={"request": request})
		return Response(serializer.data)

	def patch(self, request, pk):
		offer = get_object_or_404(Offer, pk=pk)
		if not IsOfferOwner().has_object_permission(request, self, offer):
			return Response(status=status.HTTP_403_FORBIDDEN)
		serializer = OfferUpdateSerializer(offer, data=request.data, partial=True, context={"request": request})
		serializer.is_valid(raise_exception=True)
		serializer.save()
		response_serializer = OfferCreateSerializer(offer, context={"request": request})
		return Response(response_serializer.data, status=status.HTTP_200_OK)

	def delete(self, request, pk):
		offer = get_object_or_404(Offer, pk=pk)
		if not IsOfferOwner().has_object_permission(request, self, offer):
			return Response(status=status.HTTP_403_FORBIDDEN)
		offer.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailRetrieveView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, pk):
		detail = get_object_or_404(OfferDetail, pk=pk)
		serializer = OfferDetailSerializer(detail)
		return Response(serializer.data)


class OrdersListCreateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		queryset = Order.objects.filter(
			Q(customer_user=request.user) | Q(business_user=request.user)
		)
		serializer = OrderSerializer(queryset, many=True)
		return Response(serializer.data)

	def post(self, request):
		if not IsCustomerUser().has_permission(request, self):
			return Response(status=status.HTTP_403_FORBIDDEN)
		if "offer_detail_id" not in request.data:
			return Response(status=status.HTTP_400_BAD_REQUEST)
		offer_detail = get_object_or_404(OfferDetail, pk=request.data.get("offer_detail_id"))
		order = Order.objects.create(
			customer_user=request.user,
			business_user=offer_detail.offer.user,
			title=offer_detail.title,
			revisions=offer_detail.revisions,
			delivery_time_in_days=offer_detail.delivery_time_in_days,
			price=offer_detail.price,
			features=offer_detail.features,
			offer_type=offer_detail.offer_type,
		)
		serializer = OrderSerializer(order)
		return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrdersUpdateDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def patch(self, request, pk):
		order = get_object_or_404(Order, pk=pk)
		if not IsOrderBusinessOwner().has_object_permission(request, self, order):
			return Response(status=status.HTTP_403_FORBIDDEN)
		serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
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
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		ordering = request.query_params.get("ordering")
		allowed_ordering = {"updated_at", "-updated_at", "rating", "-rating"}
		if ordering and ordering not in allowed_ordering:
			return Response(status=status.HTTP_400_BAD_REQUEST)

		queryset = Review.objects.all()
		business_user_id = request.query_params.get("business_user_id")
		if business_user_id:
			queryset = queryset.filter(business_user_id=business_user_id)
		reviewer_id = request.query_params.get("reviewer_id")
		if reviewer_id:
			queryset = queryset.filter(reviewer_id=reviewer_id)
		if ordering:
			queryset = queryset.order_by(ordering)

		serializer = ReviewSerializer(queryset, many=True)
		return Response(serializer.data)

	def post(self, request):
		if not IsCustomerUser().has_permission(request, self):
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		business_user_id = serializer.validated_data["business_user"].id
		if Review.objects.filter(business_user_id=business_user_id, reviewer=request.user).exists():
			return Response(status=status.HTTP_403_FORBIDDEN)
		review = serializer.save()
		return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewsUpdateDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def patch(self, request, pk):
		review = get_object_or_404(Review, pk=pk)
		if not IsReviewOwner().has_object_permission(request, self, review):
			return Response(status=status.HTTP_403_FORBIDDEN)
		serializer = ReviewUpdateSerializer(review, data=request.data, partial=True)
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
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.save()
		return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.validated_data, status=status.HTTP_200_OK)


class BaseInfoView(APIView):
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
