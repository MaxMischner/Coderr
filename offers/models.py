"""Offer models."""

from django.conf import settings
from django.db import models


class Offer(models.Model):
    """Offer created by a business user."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class OfferDetail(models.Model):
    """Price and delivery detail for an offer type."""
    OFFER_TYPE_BASIC = "basic"
    OFFER_TYPE_STANDARD = "standard"
    OFFER_TYPE_PREMIUM = "premium"
    OFFER_TYPE_CHOICES = [
        (OFFER_TYPE_BASIC, "Basic"),
        (OFFER_TYPE_STANDARD, "Standard"),
        (OFFER_TYPE_PREMIUM, "Premium"),
    ]

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

    def __str__(self) -> str:
        return f"{self.offer.title} - {self.offer_type}"
