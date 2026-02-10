"""Shared serializer helpers."""

from rest_framework import serializers

from ...models import OfferDetail


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


def _min_or_none(values):
    """Return min for iterable values or None if empty."""
    return min(values) if values else None


def _offer_min_price(obj):
    """Return the minimal offer price from details."""
    return _min_or_none(obj.details.values_list("price", flat=True))


def _offer_min_delivery(obj):
    """Return the minimal delivery time from offer details."""
    return _min_or_none(obj.details.values_list("delivery_time_in_days", flat=True))


def _build_user_details(user):
    """Build public user details payload for offers."""
    return {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username,
    }


def _require_offer_type(detail):
    """Return offer_type or raise a validation error."""
    offer_type = detail.get("offer_type")
    if not offer_type:
        raise serializers.ValidationError(
            "offer_type is required for detail updates.")
    return offer_type


def _get_offer_detail(instance, offer_type):
    """Fetch a detail by offer_type or raise a validation error."""
    try:
        return instance.details.get(offer_type=offer_type)
    except OfferDetail.DoesNotExist as exc:
        raise serializers.ValidationError("Offer detail not found.") from exc


def _apply_detail_update(obj, detail):
    """Apply updated fields to an offer detail instance."""
    for field, value in detail.items():
        setattr(obj, field, value)
    obj.save()


def _update_offer_details(instance, details_data):
    """Update offer details based on incoming payload."""
    for detail in details_data:
        offer_type = _require_offer_type(detail)
        obj = _get_offer_detail(instance, offer_type)
        _apply_detail_update(obj, detail)
