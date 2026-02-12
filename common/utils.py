"""Shared API helpers."""

from django.contrib.auth import get_user_model
from rest_framework import pagination, status
from rest_framework.response import Response

from profiles.models import Profile

User = get_user_model()


def _get_ordering_param(request, allowed):
    """Return ordering param and validity flag."""
    ordering = request.query_params.get("ordering")
    if ordering and ordering not in allowed:
        return ordering, False
    return ordering, True


def _apply_ordering(queryset, ordering):
    """Apply ordering when provided."""
    if ordering:
        return queryset.order_by(ordering)
    return queryset


def _paginated_response(request, queryset, serializer_cls):
    """Return a paginated response for a queryset."""
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_cls(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def _get_authenticated_user(request):
    """Return authenticated user or None."""
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return user
    return None


def _guess_profile_type(user):
    """Infer profile type from user identity hints."""
    username = (user.username or "").lower()
    email = (user.email or "").lower()
    if "customer" in username or "customer" in email:
        return Profile.TYPE_CUSTOMER
    if "business" in username or "business" in email or username.startswith("biz") or "biz" in username:
        return Profile.TYPE_BUSINESS
    return None


def _get_or_create_profile(user, default_type=None):
    """Return existing profile or create with default type."""
    try:
        return user.profile
    except Profile.DoesNotExist:
        inferred_type = _guess_profile_type(user)
        profile_type = inferred_type or default_type or Profile.TYPE_CUSTOMER
        return Profile.objects.create(user=user, type=profile_type)


def _get_business_profile_or_response(user):
    """Return business profile or a forbidden response."""
    profile = _get_or_create_profile(user, default_type=Profile.TYPE_BUSINESS)
    if profile.type != Profile.TYPE_BUSINESS:
        return None, Response(status=status.HTTP_403_FORBIDDEN)
    return profile, None


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Pagination settings for list endpoints."""
    page_size = 6
    page_size_query_param = "page_size"
