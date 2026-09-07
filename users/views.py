from rest_framework import generics, permissions

from .models import UserPreference
from .serializers import UserPreferenceSerializer


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preference, _ = UserPreference.objects.get_or_create(
            user=self.request.user
        )

        return preference