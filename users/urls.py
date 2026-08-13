from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, OrderViewSet, CartViewSet, EnquiryViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'enquiries', EnquiryViewSet, basename='enquiry')

urlpatterns = [
    path('', include(router.urls)),
]

# Made with Bob
