from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from .models import Banner, NotificationBar, LeadspaceBanner, StorySection, WhyChooseCard
from .serializers import (
     BannerSerializer, NotificationBarSerializer,
     LeadspaceBannerSerializer, StorySectionSerializer,
     WhyChooseCardSerializer, HomepageConfigSerializer
 )
from products.views import IsAdminOrReadOnly


class BannerViewSet(viewsets.ModelViewSet):
    """ViewSet for Banner operations"""
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Get active banners within date range for non-admins, all for admins"""
        if self.request.user and self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'admin':
            return Banner.objects.all().order_by('display_order', '-created_at')
            
        now = timezone.now()
        queryset = Banner.objects.filter(is_visible=True)
        
        # Filter by date range if specified
        queryset = queryset.filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )
        
        return queryset.order_by('display_order', '-created_at')


class NotificationBarViewSet(viewsets.ModelViewSet):
    """ViewSet for top notification ticker bars"""
    serializer_class = NotificationBarSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'admin':
            return NotificationBar.objects.all().order_by('display_order', '-created_at')
        return NotificationBar.objects.filter(is_active=True).order_by('display_order', '-created_at')


class LeadspaceBannerViewSet(viewsets.ModelViewSet):
    """ViewSet for Leadspace / Hero banner configuration"""
    serializer_class = LeadspaceBannerSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'admin':
            return LeadspaceBanner.objects.all().order_by('-is_active', '-created_at')
        return LeadspaceBanner.objects.filter(is_active=True).order_by('-created_at')


class StorySectionViewSet(viewsets.ModelViewSet):
    """ViewSet for Our Story section configuration"""
    serializer_class = StorySectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'admin':
            return StorySection.objects.all().order_by('-is_active', '-created_at')
        return StorySection.objects.filter(is_active=True).order_by('-created_at')


class WhyChooseCardViewSet(viewsets.ModelViewSet):
    """ViewSet for Why Choose Kasavelli cards"""
    serializer_class = WhyChooseCardSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated and getattr(self.request.user, 'role', '') == 'admin':
            return WhyChooseCard.objects.all().order_by('display_order', 'id')
        return WhyChooseCard.objects.filter(is_active=True).order_by('display_order', 'id')


class HomepageConfigViewSet(viewsets.ViewSet):
    """Aggregated endpoint to fetch active homepage sections in 1 API call"""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        notifications = NotificationBar.objects.filter(is_active=True).order_by('display_order', '-created_at')
        leadspace = LeadspaceBanner.objects.filter(is_active=True).order_by('-created_at').first()
        story = StorySection.objects.filter(is_active=True).order_by('-created_at').first()
        why_choose_cards = WhyChooseCard.objects.filter(is_active=True).order_by('display_order', 'id')

        serializer = HomepageConfigSerializer({
            'notifications': notifications,
            'leadspace': leadspace,
            'story': story,
            'why_choose_cards': why_choose_cards,
        }, context={'request': request})
        
        return Response(serializer.data)
