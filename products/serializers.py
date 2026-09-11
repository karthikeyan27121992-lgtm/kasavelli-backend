from rest_framework import serializers
from .models import Category, Product, ProductReview


def _abs_image_url(image_field, request):
    """Return absolute URL for an ImageField value, or None if empty."""
    if not image_field:
        return None
    try:
        url = image_field.url
    except ValueError:
        return None
    # Cloudinary URLs are already absolute (https://res.cloudinary.com/…).
    # Only call build_absolute_uri for relative paths (local dev media files).
    if request and not url.startswith('http'):
        return request.build_absolute_uri(url)
    return url


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_name', 'description', 'image', 'is_active', 'products_count']

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = _abs_image_url(instance.image, self.context.get('request'))
        return rep


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview model"""
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view"""
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    final_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'title', 'description', 'category', 'category_name',
            'price', 'discounted_price', 'discount_percentage', 'final_price',
            'image', 'in_stock', 'stock_quantity', 'weight', 'is_featured', 'purity', 'slug'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = _abs_image_url(instance.image, self.context.get('request'))
        return rep


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view"""
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    final_price = serializers.ReadOnlyField()
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'title', 'description', 'category', 'category_name',
            'price', 'discounted_price', 'discount_percentage', 'final_price',
            'image', 'image_2', 'image_3',
            'in_stock', 'stock_quantity', 'weight', 'purity',
            'is_featured', 'slug', 'views_count',
            'reviews', 'average_rating',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        req = self.context.get('request')
        rep['image'] = _abs_image_url(instance.image, req)
        rep['image_2'] = _abs_image_url(instance.image_2, req)
        rep['image_3'] = _abs_image_url(instance.image_3, req)
        return rep

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'title', 'description', 'category',
            'price', 'discounted_price',
            'image', 'image_2', 'image_3',
            'in_stock', 'stock_quantity', 'weight', 'purity',
            'slug', 'is_featured', 'is_active'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        req = self.context.get('request')
        rep['image'] = _abs_image_url(instance.image, req)
        rep['image_2'] = _abs_image_url(instance.image_2, req)
        rep['image_3'] = _abs_image_url(instance.image_3, req)
        return rep

# Made with Bob
