from rest_framework import generics, permissions

from .models import SavedTrack
from .serializers import SavedTrackSerializer


class SavedTrackListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedTrackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedTrack.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)