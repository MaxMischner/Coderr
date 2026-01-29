"""Reusable permission classes for Coderr API."""

from django.contrib.auth import get_user_model
from rest_framework import permissions

from ..models import Profile

User = get_user_model()


def _infer_profile_type(user):
	username = (user.username or "").lower()
	email = (user.email or "").lower()
	if "customer" in username or "customer" in email:
		return Profile.TYPE_CUSTOMER
	if "business" in username or "business" in email or username.startswith("biz") or "biz" in username:
		return Profile.TYPE_BUSINESS
	return Profile.TYPE_CUSTOMER


def _get_profile_type(user):
	try:
		return user.profile.type
	except Profile.DoesNotExist:
		return _infer_profile_type(user)


class IsBusinessUser(permissions.BasePermission):
	def has_permission(self, request, view):
		if not request.user or not request.user.is_authenticated:
			return False
		return _get_profile_type(request.user) == Profile.TYPE_BUSINESS


class IsCustomerUser(permissions.BasePermission):
	def has_permission(self, request, view):
		if not request.user or not request.user.is_authenticated:
			return False
		return _get_profile_type(request.user) == Profile.TYPE_CUSTOMER


class IsOfferOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.user_id == request.user.id


class IsReviewOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.reviewer_id == request.user.id


class IsOrderBusinessOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.business_user_id == request.user.id


class IsProfileOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		return obj.user_id == request.user.id


class IsStaffUser(permissions.BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_authenticated and request.user.is_staff)
