from rest_framework import serializers
from django.db.models import Avg
from .models import Category, Product, ProductImage, Banner, ProductReview

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
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 
            'price', 'stock_count', 'description', 'status',
            'created_at', 'updated_at', 'images', 'average_rating', 'reviews_count'
        ]
        
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_reviews_count(self, obj):
        return obj.reviews.count()
        
    def get_status(self, obj):
        if obj.stock_count == 0:
            return "OUT OF STOCK"
        elif obj.stock_count <= 2:
            return "URGENT"
        elif obj.stock_count <= 10:
            return "LOW STOCK"
        else:
            return "IN STOCK"

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image', 'link', 'is_active', 'created_at']

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_name', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'product']

    def get_user_name(self, obj):
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.username
