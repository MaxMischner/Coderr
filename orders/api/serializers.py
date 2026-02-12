"""Order serializers."""

from rest_framework import serializers

from offers.models import OfferDetail
from orders.models import Order


def _get_offer_detail_by_id(offer_detail_id):
    """Return offer detail by id or raise a validation error."""
    try:
        return OfferDetail.objects.select_related("offer", "offer__user").get(pk=offer_detail_id)
    except OfferDetail.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"offer_detail_id": "Not found."}) from exc


def _create_order_from_detail(offer_detail, user):
    """Create an order from an offer detail for the given user."""
    return Order.objects.create(
        customer_user=user,
        business_user=offer_detail.offer.user,
        title=offer_detail.title,
        revisions=offer_detail.revisions,
        delivery_time_in_days=offer_detail.delivery_time_in_days,
        price=offer_detail.price,
        features=offer_detail.features,
        offer_type=offer_detail.offer_type,
    )


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for order records."""
    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders by offer detail id."""
    offer_detail_id = serializers.IntegerField()

    def create(self, validated_data):
        offer_detail_id = validated_data["offer_detail_id"]
        offer_detail = _get_offer_detail_by_id(offer_detail_id)
        user = self.context["request"].user
        return _create_order_from_detail(offer_detail, user)


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status."""
    class Meta:
        model = Order
        fields = ["status"]
