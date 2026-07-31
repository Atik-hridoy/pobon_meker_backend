from rest_framework import serializers
from .models import Category, Product, ProductImage, Banner

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_cover']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 
            'price', 'stock_count', 'description', 'status',
            'created_at', 'updated_at', 'images'
        ]

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image', 'link', 'is_active', 'created_at']
        
    def get_status(self, obj):
        if obj.stock_count == 0:
            return "OUT OF STOCK"
        elif obj.stock_count <= 2:
            return "URGENT"
        elif obj.stock_count <= 10:
            return "LOW STOCK"
        else:
            return "IN STOCK"
