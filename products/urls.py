from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductReviewViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reviews', ProductReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]

# Made with Bob
