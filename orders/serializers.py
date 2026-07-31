from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer # Assuming this exists or I'll just return product details directly

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Unknown Product"

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'full_name', 'email', 'phone', 'address',
            'payment_method', 'applied_voucher', 'status', 'subtotal',
            'discount_amount', 'vat_amount', 'delivery_charge', 'gateway_fee',
            'grand_total', 'created_at', 'items'
        ]
