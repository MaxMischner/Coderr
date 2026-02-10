"""Review serializers."""

from rest_framework import serializers

from markt_coderr.models import Review


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
