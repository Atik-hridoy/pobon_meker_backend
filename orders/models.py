from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
import uuid

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('BKASH', 'bKash'),
        ('NAGAD', 'Nagad'),
        ('CARD', 'Card'),
    ]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Shipping Information
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()

    # Order details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    applied_voucher = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Financial Breakdown
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"PB-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Unknown Product'} for Order {self.order.order_number}"
