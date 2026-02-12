"""Profile models."""

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """User profile with customer or business type."""
    TYPE_CUSTOMER = "customer"
    TYPE_BUSINESS = "business"
    TYPE_CHOICES = [
        (TYPE_CUSTOMER, "Customer"),
        (TYPE_BUSINESS, "Business"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    file = models.ImageField(upload_to="profiles/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, default="")
    tel = models.CharField(max_length=50, blank=True, default="")
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(max_length=100, blank=True, default="")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.type})"
