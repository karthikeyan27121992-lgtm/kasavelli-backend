from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Order, OrderItem, Cart, Enquiry


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone_number', 'name', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['phone_number', 'name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'email', 'password1', 'password2', 'role'),
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_id', 'user__name', 'user__phone_number']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {'fields': ('order_id', 'user', 'total_amount', 'status')}),
        ('Shipping Info', {'fields': ('shipping_address', 'phone_number')}),
        ('Payment Info', {'fields': ('payment_id', 'payment_status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__name', 'product__name']


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__name', 'product__name', 'message']
    readonly_fields = ['created_at']

# Made with Bob
