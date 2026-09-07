from rest_framework import generics, permissions

from .models import DiscoverySession
from .serializers import DiscoverySessionSerializer


class DiscoverySessionListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = DiscoverySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiscoverySession.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)