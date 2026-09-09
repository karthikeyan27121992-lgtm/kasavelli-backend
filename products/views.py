from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, ProductReview
from .serializers import (
    CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductReviewSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to allow read-only access to all, write access to admins only"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category operations"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None  # Return all categories as a plain array, no pagination needed
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in a category"""
        category = self.get_object()
        products = Product.objects.filter(category=category, is_active=True)
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product operations"""
    queryset = Product.objects.filter(is_active=True)
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'title', 'description', 'purity', 'category__display_name', 'category__name']
    ordering_fields = ['price', 'created_at', 'views_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when product is viewed"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = Product.objects.filter(is_featured=True, is_active=True)[:10]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search products by name or description"""
        query = request.query_params.get('q', '')
        if query:
            products = Product.objects.filter(
                name__icontains=query,
                is_active=True
            ) | Product.objects.filter(
                description__icontains=query,
                is_active=True
            )
            serializer = ProductListSerializer(products.distinct(), many=True, context={'request': request})
            return Response(serializer.data)
        return Response([])
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related products from same category"""
        product = self.get_object()
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:6]
        serializer = ProductListSerializer(related_products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductReview operations"""
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.request.query_params.get('product')
        if product_id:
            return ProductReview.objects.filter(product_id=product_id)
        return ProductReview.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Made with Bob
