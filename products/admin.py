from django.contrib import admin
from .models import Category, Product, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['display_name', 'name', 'description']
    readonly_fields = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discounted_price', 'in_stock', 'is_featured', 'created_at']
    list_filter = ['category', 'in_stock', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'description', 'slug']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'slug', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price')
        }),
        ('Images', {
            'fields': ('image', 'image_2', 'image_3')
        }),
        ('Inventory', {
            'fields': ('in_stock', 'stock_quantity')
        }),
        ('Specifications', {
            'fields': ('weight', 'purity')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active', 'views_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__name', 'comment']
    readonly_fields = ['created_at']

# Made with Bob
