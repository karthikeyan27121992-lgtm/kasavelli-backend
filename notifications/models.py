from django.db import models


class Banner(models.Model):
    """Banner/Notification model for homepage"""
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='banners/')
    discount_offer = models.CharField(max_length=100, blank=True, help_text='e.g., 20% OFF, Buy 1 Get 1')
    
    # Link to product or category (optional)
    link_url = models.URLField(blank=True, null=True)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_visible = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'banners'
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title

# Made with Bob
