from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from .models import User, Order, Cart, Enquiry
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    OrderSerializer, CartSerializer, EnquirySerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User operations"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'login', 'reset_password']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Login with phone number and password"""
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone_number or not password:
            return Response(
                {'error': 'Phone number and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=phone_number, password=password)
        
        if user:
            # Auto-clear an expired spin discount at login time
            if (user.spin_discount_expires_at and
                    user.spin_discount_expires_at < timezone.now()):
                user.spin_discount_pct = 0
                user.spin_discount_expires_at = None
                user.save(update_fields=['spin_discount_pct', 'spin_discount_expires_at'])

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def reset_password(self, request):
        """Reset password by verifying phone number"""
        phone_number = request.data.get('phone_number')
        new_password = request.data.get('new_password')

        if not phone_number or not new_password:
            return Response(
                {'error': 'Phone number and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found with this phone number'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'message': 'Password reset successfully'})

    @action(detail=False, methods=['post'])
    def save_spin(self, request):
        """Save spin-wheel result for the authenticated user (24-hour validity)."""
        pct = request.data.get('percentage', 0)
        try:
            pct = int(pct)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid percentage'}, status=status.HTTP_400_BAD_REQUEST)

        if pct < 0 or pct > 100:
            return Response({'error': 'Percentage must be 0–100'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.spin_discount_pct = pct
        user.spin_discount_expires_at = timezone.now() + timedelta(hours=24) if pct > 0 else None
        user.save(update_fields=['spin_discount_pct', 'spin_discount_expires_at'])

        return Response({
            'spin_discount_pct': user.spin_discount_pct,
            'spin_discount_expires_at': user.spin_discount_expires_at,
        })

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order operations"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()
            return Response({'message': 'Order cancelled successfully'})
        return Response(
            {'error': 'Order cannot be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet for Cart operations"""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Return all cart items as a plain array

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Upsert — increment quantity if the product is already in the cart."""
        from products.models import Product
        product_id = request.data.get('product')
        try:
            quantity = max(1, int(request.data.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1

        if not product_id:
            return Response({'error': 'product is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not Product.objects.filter(id=product_id).exists():
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = self.get_serializer(cart_item, context={'request': request})
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart"""
        Cart.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart cleared successfully'})
    
    @action(detail=False, methods=['get'])
    def total(self, request):
        """Get cart total"""
        cart_items = Cart.objects.filter(user=request.user)
        total = sum(
            item.quantity * (item.product.discounted_price or item.product.price)
            for item in cart_items
        )
        return Response({'total': total, 'items_count': cart_items.count()})


class EnquiryViewSet(viewsets.ModelViewSet):
    """ViewSet for Enquiry operations"""
    serializer_class = EnquirySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Enquiry.objects.all()
        return Enquiry.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Made with Bob
