"""Profile views."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsProfileOwner
from common.utils import _get_or_create_profile
from markt_coderr.models import Profile
from profiles.api.serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileSerializer,
)

User = get_user_model()


class ProfileDetailView(APIView):
    """Retrieve and update profile details."""
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsProfileOwner()]
        return [permissions.IsAuthenticated()]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile = _get_or_create_profile(user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        profile = _get_or_create_profile(user)
        self.check_object_permissions(request, profile)
        serializer = ProfileSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BusinessProfilesListView(APIView):
    """List business profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = Profile.objects.filter(type=Profile.TYPE_BUSINESS)
        serializer = BusinessProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class CustomerProfilesListView(APIView):
    """List customer profiles."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profiles = Profile.objects.filter(type=Profile.TYPE_CUSTOMER)
        serializer = CustomerProfileListSerializer(profiles, many=True)
        return Response(serializer.data)
