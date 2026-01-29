"""Serializers for Coderr API."""

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from ..models import Offer, OfferDetail, Order, Profile, Review

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
	user = serializers.IntegerField(source="user.id", read_only=True)
	username = serializers.CharField(source="user.username", read_only=True)
	first_name = serializers.CharField(source="user.first_name", allow_blank=True, required=False)
	last_name = serializers.CharField(source="user.last_name", allow_blank=True, required=False)
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
		for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
			if data.get(key) is None:
				data[key] = ""
		return data

	def update(self, instance, validated_data):
		user_data = validated_data.pop("user", {})
		for field in ["first_name", "last_name", "email"]:
			if field in user_data:
				setattr(instance.user, field, user_data[field])
		instance.user.save()
		return super().update(instance, validated_data)


class BusinessProfileListSerializer(serializers.ModelSerializer):
	user = serializers.IntegerField(source="user.id", read_only=True)
	username = serializers.CharField(source="user.username", read_only=True)
	first_name = serializers.CharField(source="user.first_name", allow_blank=True, required=False)
	last_name = serializers.CharField(source="user.last_name", allow_blank=True, required=False)

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
		for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
			if data.get(key) is None:
				data[key] = ""
		return data


class CustomerProfileListSerializer(serializers.ModelSerializer):
	user = serializers.IntegerField(source="user.id", read_only=True)
	username = serializers.CharField(source="user.username", read_only=True)
	first_name = serializers.CharField(source="user.first_name", allow_blank=True, required=False)
	last_name = serializers.CharField(source="user.last_name", allow_blank=True, required=False)

	class Meta:
		model = Profile
		fields = ["user", "username", "first_name", "last_name", "file", "type"]

	def to_representation(self, instance):
		data = super().to_representation(instance)
		for key in ["first_name", "last_name"]:
			if data.get(key) is None:
				data[key] = ""
		return data


class OfferDetailSerializer(serializers.ModelSerializer):
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
		prices = obj.details.values_list("price", flat=True)
		return min(prices) if prices else None

	def get_min_delivery_time(self, obj):
		times = obj.details.values_list("delivery_time_in_days", flat=True)
		return min(times) if times else None

	def get_user_details(self, obj):
		return {
			"first_name": obj.user.first_name or "",
			"last_name": obj.user.last_name or "",
			"username": obj.user.username,
		}


class OfferDetailViewSerializer(serializers.ModelSerializer):
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
		prices = obj.details.values_list("price", flat=True)
		return min(prices) if prices else None

	def get_min_delivery_time(self, obj):
		times = obj.details.values_list("delivery_time_in_days", flat=True)
		return min(times) if times else None


class OfferCreateSerializer(serializers.ModelSerializer):
	details = OfferDetailSerializer(many=True)

	class Meta:
		model = Offer
		fields = ["id", "title", "image", "description", "details"]

	def validate_details(self, value):
		if len(value) != 3:
			raise serializers.ValidationError("An offer must contain exactly 3 details.")
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
	details = OfferDetailSerializer(many=True, required=False)

	class Meta:
		model = Offer
		fields = ["title", "image", "description", "details"]

	@transaction.atomic
	def update(self, instance, validated_data):
		details_data = validated_data.pop("details", None)
		instance = super().update(instance, validated_data)
		if details_data is not None:
			for detail in details_data:
				offer_type = detail.get("offer_type")
				if not offer_type:
					raise serializers.ValidationError("offer_type is required for detail updates.")
				try:
					obj = instance.details.get(offer_type=offer_type)
				except OfferDetail.DoesNotExist as exc:
					raise serializers.ValidationError("Offer detail not found.") from exc
				for field, value in detail.items():
					setattr(obj, field, value)
				obj.save()
		return instance


class OrderSerializer(serializers.ModelSerializer):
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
	offer_detail_id = serializers.IntegerField()

	def create(self, validated_data):
		offer_detail_id = validated_data["offer_detail_id"]
		try:
			offer_detail = OfferDetail.objects.select_related("offer", "offer__user").get(
				pk=offer_detail_id
			)
		except OfferDetail.DoesNotExist as exc:
			raise serializers.ValidationError({"offer_detail_id": "Not found."}) from exc
		user = self.context["request"].user
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


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Order
		fields = ["status"]


class ReviewSerializer(serializers.ModelSerializer):
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
	class Meta:
		model = Review
		fields = ["business_user", "rating", "description"]

	def validate_rating(self, value):
		if value < 1 or value > 5:
			raise serializers.ValidationError("Rating must be between 1 and 5.")
		return value

	def create(self, validated_data):
		user = self.context["request"].user
		return Review.objects.create(reviewer=user, **validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Review
		fields = ["rating", "description"]

	def validate_rating(self, value):
		if value < 1 or value > 5:
			raise serializers.ValidationError("Rating must be between 1 and 5.")
		return value


class RegistrationSerializer(serializers.Serializer):
	username = serializers.CharField()
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True)
	repeated_password = serializers.CharField(write_only=True)
	type = serializers.ChoiceField(choices=Profile.TYPE_CHOICES)

	def validate(self, attrs):
		if attrs["password"] != attrs["repeated_password"]:
			raise serializers.ValidationError({"repeated_password": "Passwords do not match."})
		return attrs

	@transaction.atomic
	def create(self, validated_data):
		password = validated_data.pop("password")
		validated_data.pop("repeated_password")
		profile_type = validated_data.pop("type")
		user = User.objects.create_user(password=password, **validated_data)
		Profile.objects.create(user=user, type=profile_type)
		token, _ = Token.objects.get_or_create(user=user)
		return {
			"token": token.key,
			"username": user.username,
			"email": user.email,
			"user_id": user.pk,
		}


class LoginSerializer(serializers.Serializer):
	username = serializers.CharField()
	password = serializers.CharField(write_only=True)

	def validate(self, attrs):
		user = authenticate(username=attrs["username"], password=attrs["password"])
		if not user:
			raise serializers.ValidationError("Invalid credentials")
		token, _ = Token.objects.get_or_create(user=user)
		return {
			"token": token.key,
			"username": user.username,
			"email": user.email,
			"user_id": user.pk,
		}


class BaseInfoSerializer(serializers.Serializer):
	review_count = serializers.IntegerField()
	average_rating = serializers.FloatField()
	business_profile_count = serializers.IntegerField()
	offer_count = serializers.IntegerField()
