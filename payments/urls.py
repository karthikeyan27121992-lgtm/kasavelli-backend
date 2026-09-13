from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, razorpay_webhook

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    # Razorpay webhook — CSRF-exempt, verified via HMAC-SHA256 signature
    path('webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('', include(router.urls)),
]

# Made with Bob
