"""Database models for Coderr backend."""

from django.conf import settings
from django.db import models


class Profile(models.Model):
	TYPE_CUSTOMER = "customer"
	TYPE_BUSINESS = "business"
	TYPE_CHOICES = [
		(TYPE_CUSTOMER, "Customer"),
		(TYPE_BUSINESS, "Business"),
	]

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	file = models.ImageField(upload_to="profiles/", blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, default="")
	tel = models.CharField(max_length=50, blank=True, default="")
	description = models.TextField(blank=True, default="")
	working_hours = models.CharField(max_length=100, blank=True, default="")
	type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.user.username} ({self.type})"


class Offer(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offers")
	title = models.CharField(max_length=255)
	image = models.ImageField(upload_to="offers/", blank=True, null=True)
	description = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.title


class OfferDetail(models.Model):
	OFFER_TYPE_BASIC = "basic"
	OFFER_TYPE_STANDARD = "standard"
	OFFER_TYPE_PREMIUM = "premium"
	OFFER_TYPE_CHOICES = [
		(OFFER_TYPE_BASIC, "Basic"),
		(OFFER_TYPE_STANDARD, "Standard"),
		(OFFER_TYPE_PREMIUM, "Premium"),
	]

	offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
	title = models.CharField(max_length=255)
	revisions = models.IntegerField()
	delivery_time_in_days = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	features = models.JSONField(default=list, blank=True)
	offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

	def __str__(self) -> str:
		return f"{self.offer.title} - {self.offer_type}"


class Order(models.Model):
	STATUS_IN_PROGRESS = "in_progress"
	STATUS_COMPLETED = "completed"
	STATUS_CANCELLED = "cancelled"
	STATUS_CHOICES = [
		(STATUS_IN_PROGRESS, "In Progress"),
		(STATUS_COMPLETED, "Completed"),
		(STATUS_CANCELLED, "Cancelled"),
	]

	customer_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="customer_orders",
	)
	business_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="business_orders",
	)
	title = models.CharField(max_length=255)
	revisions = models.IntegerField()
	delivery_time_in_days = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	features = models.JSONField(default=list, blank=True)
	offer_type = models.CharField(max_length=20)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"Order #{self.pk} ({self.status})"


class Review(models.Model):
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
