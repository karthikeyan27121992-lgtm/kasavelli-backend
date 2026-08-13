from django.contrib import admin
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_offer', 'is_visible', 'display_order', 'start_date', 'end_date']
    list_filter = ['is_visible', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'discount_offer']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'description', 'image', 'discount_offer')
        }),
        ('Link', {
            'fields': ('link_url', 'product')
        }),
        ('Display Settings', {
            'fields': ('is_visible', 'display_order', 'start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Made with Bob
