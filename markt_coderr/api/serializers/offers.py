"""Offer serializers."""

from django.db import transaction
from rest_framework import serializers

from ...models import Offer, OfferDetail
from .utils import (
    _offer_min_delivery,
    _offer_min_price,
    _build_user_details,
    _update_offer_details,
)


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
