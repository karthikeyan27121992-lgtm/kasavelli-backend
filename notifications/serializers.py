from rest_framework import serializers
from .models import Banner
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

# Made with Bob
