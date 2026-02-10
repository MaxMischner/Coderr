"""Profile serializers."""

from rest_framework import serializers

from markt_coderr.models import Profile


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
