from rest_framework import viewsets, permissions
from django.utils import timezone
from django.db import models
from .models import Banner
from .serializers import BannerSerializer
from products.views import IsAdminOrReadOnly


class BannerViewSet(viewsets.ModelViewSet):
    """ViewSet for Banner operations"""
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Get active banners within date range"""
        now = timezone.now()
        queryset = Banner.objects.filter(is_visible=True)
        
        # Filter by date range if specified
        queryset = queryset.filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )
        
        return queryset.order_by('display_order', '-created_at')

# Made with Bob
