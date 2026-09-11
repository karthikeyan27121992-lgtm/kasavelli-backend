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
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
    
    def __str__(self):
        return self.title


class NotificationBar(models.Model):
    """Top notification ticker bar content"""
    text = models.TextField(help_text='Notification announcement text')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_bars'
        ordering = ['display_order', '-created_at']
        verbose_name = 'Notification Bar'
        verbose_name_plural = 'Notification Bars'

    def __str__(self):
        return self.text[:50]


class LeadspaceBanner(models.Model):
    """Hero / Leadspace banner section configuration"""
    eyebrow = models.CharField(max_length=100, default='New Collection · 2026')
    title = models.CharField(max_length=255, default='Vanki Rings')
    desc_line1 = models.CharField(max_length=255, default='Traditional South Indian finger rings, handcrafted in 925 sterling silver.')
    desc_line2 = models.CharField(max_length=255, blank=True, default='Worn with mehndi or bridal wear — a timeless symbol of grace.')
    offer_pct = models.CharField(max_length=50, blank=True, default='20% OFF')
    offer_label = models.CharField(max_length=150, blank=True, default='on all Vanki Rings · Limited Time')
    button_text = models.CharField(max_length=50, default='Shop Now')
    button_link = models.CharField(max_length=255, default='/products')
    image = models.ImageField(upload_to='leadspace/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, help_text='External/asset image URL or fallback')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leadspace_banners'
        ordering = ['-is_active', '-created_at']
        verbose_name = 'Leadspace Banner'
        verbose_name_plural = 'Leadspace Banners'

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class StorySection(models.Model):
    """Our Story / About section configuration"""
    eyebrow = models.CharField(max_length=100, default='Our Story')
    title = models.CharField(max_length=255, default='Crafted with Passion, Worn with Pride')
    paragraph_1 = models.TextField(default='Founded in 2024, Kasavelli was born from a love for traditional Indian jewellery-making. Every piece is handcrafted by skilled artisans using 925 hallmarked sterling silver — hypoallergenic, durable, and timeless.')
    paragraph_2 = models.TextField(blank=True, default='We blend centuries-old craftsmanship with modern design sensibilities to create jewellery that tells a story. From bridal sets to everyday wear, each Kasavelli piece is a work of art.')
    
    # Badge details on image
    badge_number = models.CharField(max_length=50, default='925')
    badge_label = models.CharField(max_length=100, default='Hallmarked Silver')
    
    # Stats
    stat1_value = models.CharField(max_length=50, default='100+')
    stat1_label = models.CharField(max_length=100, default='Unique Designs')
    stat2_value = models.CharField(max_length=50, default='500+')
    stat2_label = models.CharField(max_length=100, default='Happy Customers')
    stat3_value = models.CharField(max_length=50, default='925')
    stat3_label = models.CharField(max_length=100, default='Silver Purity')
    
    button_text = models.CharField(max_length=50, default='View Collection')
    button_link = models.CharField(max_length=255, default='/products')
    image = models.ImageField(upload_to='story/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, help_text='External/asset image URL or fallback')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'story_sections'
        ordering = ['-is_active', '-created_at']
        verbose_name = 'Story Section'
        verbose_name_plural = 'Story Sections'

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class WhyChooseCard(models.Model):
    """Cards for 'Why Choose Kasavelli' section"""
    ICON_CHOICES = [
        ('shield', 'Shield / Certified'),
        ('heart', 'Heart / Handpicked'),
        ('truck', 'Truck / Delivery'),
        ('returns', 'Trending / 30-Day Returns'),
        ('gift', 'Gift / Packaging'),
        ('sparkles', 'Sparkles / Made in India'),
        ('custom', 'Custom Icon'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField()
    icon_type = models.CharField(max_length=50, choices=ICON_CHOICES, default='shield')
    custom_icon_svg = models.TextField(blank=True, help_text='Optional custom SVG path or raw SVG')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'why_choose_cards'
        ordering = ['display_order', 'id']
        verbose_name = 'Why Choose Card'
        verbose_name_plural = 'Why Choose Cards'

    def __str__(self):
        return self.title
