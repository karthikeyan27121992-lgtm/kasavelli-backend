from rest_framework import serializers
from .models import Category, Product, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    products_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'display_name', 'description', 'image', 'is_active', 'products_count']

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'title', 'category', 'category_name',
            'price', 'discounted_price', 'discount_percentage', 'final_price',
            'image', 'in_stock', 'is_featured', 'purity', 'slug'
        ]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view"""
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    final_price = serializers.ReadOnlyField()
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image_2 = serializers.SerializerMethodField()
    image_3 = serializers.SerializerMethodField()

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

    def _abs_url(self, field_value):
        if not field_value:
            return None
        request = self.context.get('request')
        url = field_value.url
        return request.build_absolute_uri(url) if request else url

    def get_image(self, obj):
        return self._abs_url(obj.image)

    def get_image_2(self, obj):
        return self._abs_url(obj.image_2)

    def get_image_3(self, obj):
        return self._abs_url(obj.image_3)

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

# Made with Bob
