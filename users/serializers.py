from rest_framework import serializers
from django.conf import settings
from .models import User, Order, OrderItem, Cart, Enquiry


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'name', 'email', 'role', 'date_joined',
            'spin_discount_pct', 'spin_discount_expires_at',
        ]
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['phone_number', 'name', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            phone_number=validated_data['phone_number'],
            name=validated_data['name'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'user_name', 'total_amount', 
            'status', 'shipping_address', 'phone_number', 
            'payment_id', 'payment_status', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_id', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart model"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    discounted_price = serializers.DecimalField(source='product.discounted_price', max_digits=10, decimal_places=2, read_only=True)

    def get_product_image(self, obj):
        request = self.context.get('request')
        if not obj.product.image:
            return None
        url = obj.product.image.url
        if request:
            try:
                return request.build_absolute_uri(url)
            except Exception:
                pass
        return f"http://localhost:8000{url}"
    
    class Meta:
        model = Cart
        fields = [
            'id', 'product', 'product_name', 'product_price', 
            'product_image', 'discounted_price', 'quantity', 'added_at'
        ]
        read_only_fields = ['id', 'added_at']


class EnquirySerializer(serializers.ModelSerializer):
    """Serializer for Enquiry model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Enquiry
        fields = ['id', 'user', 'user_name', 'product', 'product_name', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']

# Made with Bob
