from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BannerViewSet,
    NotificationBarViewSet,
    LeadspaceBannerViewSet,
    StorySectionViewSet,
    WhyChooseCardViewSet,
    HomepageConfigViewSet,
)

router = DefaultRouter()
router.register(r'banners', BannerViewSet, basename='banner')
router.register(r'notification-bars', NotificationBarViewSet, basename='notification-bar')
router.register(r'leadspace-banners', LeadspaceBannerViewSet, basename='leadspace-banner')
router.register(r'story-sections', StorySectionViewSet, basename='story-section')
router.register(r'why-choose-cards', WhyChooseCardViewSet, basename='why-choose-card')
router.register(r'homepage-config', HomepageConfigViewSet, basename='homepage-config')

urlpatterns = [
    path('', include(router.urls)),
]
