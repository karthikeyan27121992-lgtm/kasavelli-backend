from django.contrib import admin
from .models import Banner, NotificationBar, LeadspaceBanner, StorySection, WhyChooseCard


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_offer', 'is_visible', 'display_order', 'start_date', 'end_date']
    list_filter = ['is_visible', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    list_editable = ['is_visible', 'display_order']


@admin.register(NotificationBar)
class NotificationBarAdmin(admin.ModelAdmin):
    list_display = ['id', 'text', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['text']
    list_editable = ['is_active', 'display_order']


@admin.register(LeadspaceBanner)
class LeadspaceBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'eyebrow', 'offer_pct', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'eyebrow', 'desc_line1']
    list_editable = ['is_active']


@admin.register(StorySection)
class StorySectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'eyebrow', 'stat1_value', 'stat2_value', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'paragraph_1']
    list_editable = ['is_active']


@admin.register(WhyChooseCard)
class WhyChooseCardAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon_type', 'display_order', 'is_active']
    list_filter = ['is_active', 'icon_type']
    search_fields = ['title', 'description']
    list_editable = ['display_order', 'is_active']
