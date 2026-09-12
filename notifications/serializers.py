from rest_framework import serializers
from .models import Banner, NotificationBar, LeadspaceBanner, StorySection, WhyChooseCard, SpinWheelSlice
from products.serializers import _abs_image_url


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner model"""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'description', 'image', 'discount_offer',
            'link_url', 'product', 'product_name', 'is_visible',
            'display_order', 'start_date', 'end_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = _abs_image_url(instance.image, self.context.get('request'))
        return rep


class NotificationBarSerializer(serializers.ModelSerializer):
    """Serializer for NotificationBar model"""
    class Meta:
        model = NotificationBar
        fields = ['id', 'text', 'is_active', 'display_order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeadspaceBannerSerializer(serializers.ModelSerializer):
    """Serializer for LeadspaceBanner model"""
    class Meta:
        model = LeadspaceBanner
        fields = [
            'id', 'eyebrow', 'title', 'desc_line1', 'desc_line2',
            'offer_pct', 'offer_label', 'button_text', 'button_link',
            'image', 'image_url', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = _abs_image_url(instance.image, self.context.get('request'))
        # If image is absent, rep['image'] might be None or fallback to image_url
        if not rep.get('image') and instance.image_url:
            rep['image'] = instance.image_url
        return rep


class StorySectionSerializer(serializers.ModelSerializer):
    """Serializer for StorySection model"""
    class Meta:
        model = StorySection
        fields = [
            'id', 'eyebrow', 'title', 'paragraph_1', 'paragraph_2',
            'badge_number', 'badge_label',
            'stat1_value', 'stat1_label',
            'stat2_value', 'stat2_label',
            'stat3_value', 'stat3_label',
            'button_text', 'button_link',
            'image', 'image_url', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['image'] = _abs_image_url(instance.image, self.context.get('request'))
        if not rep.get('image') and instance.image_url:
            rep['image'] = instance.image_url
        return rep


class WhyChooseCardSerializer(serializers.ModelSerializer):
    """Serializer for WhyChooseCard model"""
    class Meta:
        model = WhyChooseCard
        fields = [
            'id', 'title', 'description', 'icon_type',
            'custom_icon_svg', 'display_order', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SpinWheelSliceSerializer(serializers.ModelSerializer):
    """Serializer for SpinWheelSlice model"""
    class Meta:
        model = SpinWheelSlice
        fields = [
            'id', 'label', 'percentage', 'color', 'text_color',
            'display_order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HomepageConfigSerializer(serializers.Serializer):
    """Consolidated homepage config serializer for single-fetch frontend efficiency"""
    notifications = NotificationBarSerializer(many=True)
    leadspace = LeadspaceBannerSerializer(allow_null=True)
    story = StorySectionSerializer(allow_null=True)
    why_choose_cards = WhyChooseCardSerializer(many=True)
    spin_wheel_slices = SpinWheelSliceSerializer(many=True)
