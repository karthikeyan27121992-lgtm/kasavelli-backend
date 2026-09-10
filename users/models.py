from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for phone number authentication"""
    
    def create_user(self, phone_number, name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        
        user = self.model(
            phone_number=phone_number,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with phone number authentication"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    phone_number = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # Spin-wheel discount — set on spin, cleared automatically after 24 h
    spin_discount_pct = models.PositiveSmallIntegerField(default=0)
    spin_discount_expires_at = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class Order(models.Model):
    """Order model to track user purchases"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_id = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=50, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_id} - {self.user.name}"


class OrderItem(models.Model):
    """Order items model"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Cart(models.Model):
    """Shopping cart model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart'
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.name} - {self.product.name}"


class Enquiry(models.Model):
    """Product enquiry model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enquiries')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'enquiries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Enquiry by {self.user.name} for {self.product.name}"

# Made with Bob
