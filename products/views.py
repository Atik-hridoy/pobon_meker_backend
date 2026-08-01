from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Category, Product, ProductImage, Banner, ProductReview
from .serializers import CategorySerializer, ProductSerializer, BannerSerializer, ProductReviewSerializer
from .pagination import ProductPagination
from core.responses import StandardResponse

class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Categories retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
        
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Products retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        
        # Handle images
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            # First image is cover
            is_cover = (i == 0)
            ProductImage.objects.create(product=product, image=image, is_cover=is_cover)
            
        return StandardResponse(
            success=True,
            message="Product created successfully.",
            data=self.get_serializer(product).data,
            status=status.HTTP_201_CREATED
        )

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Product retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Handle optional new images
        images = request.FILES.getlist('images')
        if images:
            # Optionally clear old images, or just append
            instance.images.all().delete()
            for i, image in enumerate(images):
                is_cover = (i == 0)
                ProductImage.objects.create(product=instance, image=image, is_cover=is_cover)

        return StandardResponse(
            success=True,
            message="Product updated successfully.",
            data=self.get_serializer(instance).data,
            status=status.HTTP_200_OK
        )
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return StandardResponse(
            success=True,
            message="Product deleted successfully.",
            data=None,
            status=status.HTTP_204_NO_CONTENT
        )

class BannerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Banner.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = BannerSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Banners retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist('images')
        if not images:
            return Response({'image': ['No file was submitted.']}, status=status.HTTP_400_BAD_REQUEST)
            
        # Replace existing banners
        Banner.objects.all().delete()
        
        created_banners = []
        for image in images:
            banner = Banner.objects.create(image=image, is_active=True)
            created_banners.append(banner)
            
        serializer = self.get_serializer(created_banners, many=True)
        return StandardResponse(
            success=True,
            message="Banners created successfully.",
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

class PublicProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Public products retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]
        
    def get_queryset(self):
        product_id = self.kwargs.get('pk')
        return ProductReview.objects.filter(product_id=product_id).order_by('-created_at')
        
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Reviews retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )
        
    def create(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not rating or not (1 <= int(rating) <= 5):
            return Response({'error': 'Valid rating (1-5) is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if already reviewed
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return Response({'error': 'You have already reviewed this product'}, status=status.HTTP_400_BAD_REQUEST)
            
        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=int(rating),
            comment=comment
        )
        
        serializer = self.get_serializer(review)
        return StandardResponse(
            success=True,
            message="Review submitted successfully.",
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

class BestSellingProductsAPIView(generics.ListAPIView):
    """
    Returns best-selling products calculated from real order data.
    
    Logic:
    1. Aggregates total quantity sold per product from OrderItem table
    2. Only counts items from non-cancelled orders
    3. Falls back to highest-rated products if insufficient order data
    4. Supports ?limit=N query param (default 12)
    """
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from django.db.models import Sum, Q, Value, IntegerField
        from django.db.models.functions import Coalesce
        from orders.models import OrderItem

        limit = int(self.request.query_params.get('limit', 12))

        # Annotate each product with total_sold from non-cancelled orders
        queryset = Product.objects.annotate(
            total_sold=Coalesce(
                Sum(
                    'orderitem__quantity',
                    filter=~Q(orderitem__order__status='CANCELLED')
                ),
                Value(0),
                output_field=IntegerField()
            )
        ).order_by('-total_sold', '-created_at')

        # If no products have been sold yet, fall back to highest-rated
        top_products = queryset[:limit]
        if all(p.total_sold == 0 for p in top_products):
            from django.db.models import Avg
            queryset = Product.objects.annotate(
                avg_rating=Coalesce(Avg('reviews__rating'), Value(0.0))
            ).order_by('-avg_rating', '-created_at')

        return queryset[:limit]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return StandardResponse(
            success=True,
            message="Best selling products retrieved successfully.",
            data=serializer.data,
            status=status.HTTP_200_OK
        )
