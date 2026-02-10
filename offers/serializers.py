"""Offer serializers."""

from django.db import transaction
from rest_framework import serializers

from markt_coderr.models import Offer, OfferDetail


def _min_or_none(values):
    """Return min for iterable values or None if empty."""
    return min(values) if values else None


def _offer_min_price(obj):
    """Return the minimal offer price from details."""
    return _min_or_none(obj.details.values_list("price", flat=True))


def _offer_min_delivery(obj):
    """Return the minimal delivery time from offer details."""
    return _min_or_none(obj.details.values_list("delivery_time_in_days", flat=True))


def _build_user_details(user):
    """Build public user details payload for offers."""
    return {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username,
    }


def _require_offer_type(detail):
    """Return offer_type or raise a validation error."""
    offer_type = detail.get("offer_type")
    if not offer_type:
        raise serializers.ValidationError(
            "offer_type is required for detail updates.")
    return offer_type


def _get_offer_detail(instance, offer_type):
    """Fetch a detail by offer_type or raise a validation error."""
    try:
        return instance.details.get(offer_type=offer_type)
    except OfferDetail.DoesNotExist as exc:
        raise serializers.ValidationError("Offer detail not found.") from exc


def _apply_detail_update(obj, detail):
    """Apply updated fields to an offer detail instance."""
    for field, value in detail.items():
        setattr(obj, field, value)
    obj.save()


def _update_offer_details(instance, details_data):
    """Update offer details based on incoming payload."""
    for detail in details_data:
        offer_type = _require_offer_type(detail)
        obj = _get_offer_detail(instance, offer_type)
        _apply_detail_update(obj, detail)


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer for offer detail data."""
    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Serializer that exposes offer detail link."""
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        request = self.context.get("request")
        path = f"/api/offerdetails/{obj.pk}/"
        if request is None:
            return path
        return request.build_absolute_uri(path)


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for offer list results."""
    user = serializers.IntegerField(source="user.id", read_only=True)
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]

    def get_min_price(self, obj):
        return _offer_min_price(obj)

    def get_min_delivery_time(self, obj):
        return _offer_min_delivery(obj)

    def get_user_details(self, obj):
        return _build_user_details(obj.user)


class OfferDetailViewSerializer(serializers.ModelSerializer):
    """Serializer for offer detail views."""
    user = serializers.IntegerField(source="user.id", read_only=True)
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
        ]

    def get_min_price(self, obj):
        return _offer_min_price(obj)

    def get_min_delivery_time(self, obj):
        return _offer_min_delivery(obj)


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating offers with details."""
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        if len(value) != 3:
            raise serializers.ValidationError(
                "An offer must contain exactly 3 details.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop("details")
        user = self.context["request"].user
        offer = Offer.objects.create(user=user, **validated_data)
        for detail in details_data:
            OfferDetail.objects.create(offer=offer, **detail)
        return offer


class OfferUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating offers and details."""
    details = OfferDetailSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ["title", "image", "description", "details"]

    @transaction.atomic
    def update(self, instance, validated_data):
        details_data = validated_data.pop("details", None)
        instance = super().update(instance, validated_data)
        if details_data is not None:
            _update_offer_details(instance, details_data)
        return instance
