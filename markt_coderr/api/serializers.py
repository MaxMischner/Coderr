"""Serializers for Coderr API."""

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from ..models import Offer, OfferDetail, Order, Profile, Review

User = get_user_model()


def _normalize_nulls(data, keys):
    """Replace null values with empty strings for selected keys."""
    for key in keys:
        if data.get(key) is None:
            data[key] = ""
    return data


def _update_user_fields(user, user_data, fields):
    """Update user fields from nested payload data."""
    for field in fields:
        if field in user_data:
            setattr(user, field, user_data[field])
    user.save()


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


def _create_user_with_profile(validated_data):
    """Create user and profile from registration payload."""
    password = validated_data.pop("password")
    validated_data.pop("repeated_password")
    profile_type = validated_data.pop("type")
    user = User.objects.create_user(password=password, **validated_data)
    Profile.objects.create(user=user, type=profile_type)
    return user


def _build_auth_response(user):
    """Build authentication response payload with token."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.pk,
    }


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for full profile details."""
    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", allow_blank=True, required=False)
    last_name = serializers.CharField(
        source="user.last_name", allow_blank=True, required=False)
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        model = Profile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]
        read_only_fields = ["created_at", "user", "username"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        keys = ["first_name", "last_name", "location",
                "tel", "description", "working_hours"]
        return _normalize_nulls(data, keys)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        _update_user_fields(instance.user, user_data, [
                            "first_name", "last_name", "email"])
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Serializer for listing business profiles."""
    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", allow_blank=True, required=False)
    last_name = serializers.CharField(
        source="user.last_name", allow_blank=True, required=False)

    class Meta:
        model = Profile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        keys = ["first_name", "last_name", "location",
                "tel", "description", "working_hours"]
        return _normalize_nulls(data, keys)


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Serializer for listing customer profiles."""
    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", allow_blank=True, required=False)
    last_name = serializers.CharField(
        source="user.last_name", allow_blank=True, required=False)

    class Meta:
        model = Profile
        fields = ["user", "username", "first_name",
                  "last_name", "file", "type"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return _normalize_nulls(data, ["first_name", "last_name"])


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


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for review records."""
    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reviewer", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    class Meta:
        model = Review
        fields = ["business_user", "rating", "description"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return Review.objects.create(reviewer=user, **validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reviews."""
    class Meta:
        model = Review
        fields = ["rating", "description"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5.")
        return value


class RegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=Profile.TYPE_CHOICES)

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = _create_user_with_profile(validated_data)
        return _build_auth_response(user)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        return _build_auth_response(user)


class BaseInfoSerializer(serializers.Serializer):
    """Serializer for base info statistics."""
    review_count = serializers.IntegerField()
    average_rating = serializers.FloatField()
    business_profile_count = serializers.IntegerField()
    offer_count = serializers.IntegerField()
