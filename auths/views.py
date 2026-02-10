"""Authentication views."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from auths.serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """Register a new user and return token."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return token."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
