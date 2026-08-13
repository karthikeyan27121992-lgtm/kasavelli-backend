from django.db import models


class Category(models.Model):
    """Product category model"""
    
    CATEGORY_CHOICES = [
        ('chain-with-pendant', 'Chain with Pendant'),
        ('earrings', 'Ear Rings'),
        ('pendant', 'Pendant'),
        ('gold-polish', 'Gold Polish Looks'),
        ('rings', 'Rings'),
        ('anklets', 'Anklets'),
        ('bracelets', 'Bracelets'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.display_name


class Product(models.Model):
    """Product model for silver jewellery"""
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    image = models.ImageField(upload_to='products/')
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)
    
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    
    # Product specifications
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='Weight in grams')
    purity = models.CharField(max_length=50, default='925 Silver')
    
    # SEO and metadata
    slug = models.SlugField(max_length=255, unique=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.discounted_price and self.price:
            return round(((self.price - self.discounted_price) / self.price) * 100, 2)
        return 0
    
    @property
    def final_price(self):
        """Get final price (discounted or regular)"""
        return self.discounted_price if self.discounted_price else self.price


class ProductReview(models.Model):
    """Product review model"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_reviews'
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.product.name} ({self.rating}★)"

# Made with Bob
