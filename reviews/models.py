"""Review models."""

from django.conf import settings
from django.db import models


class Review(models.Model):
    """Review left by a customer for a business user."""
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveIntegerField()
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("business_user", "reviewer")

    def __str__(self) -> str:
        return f"Review {self.rating}/5 by {self.reviewer}"
