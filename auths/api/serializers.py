"""Authentication serializers."""

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from profiles.models import Profile

User = get_user_model()


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
