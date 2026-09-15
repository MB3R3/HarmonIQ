from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SpotifyConnection, UserPreference
from .serializers import UserPreferenceSerializer


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preference, _ = UserPreference.objects.get_or_create(
            user=self.request.user
        )

        return preference

    def delete(self, request, *args, **kwargs):
        """Reset saved preferences to model defaults without touching the
        user account, Spotify connection, or saved tracks."""

        preference = self.get_object()
        preference.favorite_genres = []
        preference.preferred_eras = []
        preference.default_mood = ""

        discovery_style_default = UserPreference._meta.get_field(
            "discovery_style"
        ).default
        frequency_default = UserPreference._meta.get_field(
            "recommendation_frequency"
        ).default
        preference.discovery_style = discovery_style_default
        preference.recommendation_frequency = frequency_default
        preference.save()

        return Response(
            UserPreferenceSerializer(preference).data,
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = []

    def get(self, request):
        user = request.user

        if not user.is_authenticated:
            return Response(
                {
                    "authenticated": False,
                    "user": None,
                }
            )

        return Response(
            {
                "authenticated": True,
                "user": self._safe_profile(user),
            }
        )

    def _safe_profile(self, user):
        connection = SpotifyConnection.objects.filter(user=user).first()
        return {
            "id": user.pk,
            "username": user.username,
            "email": user.email,
            "spotify_connected": connection is not None,
            # Display name only — never tokens.
            "spotify_display_name": (
                connection.spotify_display_name
                if connection and connection.spotify_display_name
                else None
            ),
        }


class SignupView(APIView):
    """Create a HarmonIQ account and start a Django session.

    The Django username is always the HarmonIQ username chosen here — it is
    independent of any Spotify identity linked later.
    """

    permission_classes = []

    def post(self, request):
        data = request.data or {}

        username = str(data.get("username", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        missing = self._validate_presence(
            username, email, password, password_confirm
        )
        if missing:
            return missing

        try:
            validate_email(email)
        except ValidationError:
            return self._error(
                "Enter a valid email address.",
                status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return self._error(
                "That username is already taken.",
                status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email__iexact=email).exists():
            return self._error(
                "An account with that email already exists.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password)
        except ValidationError as exc:
            return self._error(
                " ".join(exc.messages),
                status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # Establish the Django session so the new account is authenticated
        # immediately (same architecture as LoginView).
        django_login(request, user)

        return Response(
            {
                "authenticated": True,
                "user": CurrentUserView()._safe_profile(user),
            },
            status=status.HTTP_201_CREATED,
        )

    def _validate_presence(self, username, email, password, password_confirm):
        if not username:
            return self._error(
                "Username is required.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not email:
            return self._error(
                "Email is required.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return self._error(
                "Password is required.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not password_confirm:
            return self._error(
                "Please confirm your password.",
                status.HTTP_400_BAD_REQUEST,
            )
        if password != password_confirm:
            return self._error(
                "Passwords do not match.",
                status.HTTP_400_BAD_REQUEST,
            )
        return None

    @staticmethod
    def _error(message, http_status):
        return Response(
            {
                "authenticated": False,
                "error": message,
            },
            status=http_status,
        )


class LoginView(APIView):
    """Authenticate credentials and start a Django session."""

    permission_classes = []

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {
                    "authenticated": False,
                    "error": "Username and password are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "authenticated": False,
                    "error": "Invalid username or password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        django_login(request, user)

        return Response(
            {
                "authenticated": True,
                "user": CurrentUserView()._safe_profile(user),
            }
        )


class LogoutView(APIView):
    """End the Django session using the existing session architecture."""

    permission_classes = []

    def post(self, request):
        django_logout(request)
        return Response(
            {
                "authenticated": False,
                "user": None,
            }
        )