"""Order views."""

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCustomerUser, IsOrderBusinessOwner, IsStaffUser
from common.utils import _get_or_create_profile
from offers.models import OfferDetail
from orders.models import Order
from profiles.models import Profile
from orders.api.serializers import OrderSerializer, OrderStatusUpdateSerializer

User = get_user_model()


def _orders_for_user(user):
    """Return orders where user is customer or business."""
    return Order.objects.filter(Q(customer_user=user) | Q(business_user=user))


def _get_offer_detail_or_response(request):
    """Return offer detail or a bad request response."""
    if "offer_detail_id" not in request.data:
        return None, Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        offer_detail_id = request.data.get("offer_detail_id")
        offer_detail = get_object_or_404(OfferDetail, pk=offer_detail_id)
    except (TypeError, ValueError):
        return None, Response(status=status.HTTP_400_BAD_REQUEST)
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
