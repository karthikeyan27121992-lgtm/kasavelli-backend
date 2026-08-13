from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['razorpay_order_id', 'razorpay_payment_id', 'order__order_id']
    readonly_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order', 'amount', 'currency')
        }),
        ('Razorpay Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Status', {
            'fields': ('status', 'payment_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Made with Bob
