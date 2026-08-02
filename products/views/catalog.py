from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from products.models import Product, ProductImage
from products.serializers import ProductSerializer
from products.pagination import ProductPagination
from core.responses import StandardResponse

class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('category').prefetch_related('images').all().order_by('-created_at')
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

class PublicProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPagination

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')
        # Support multiple ?category=A&category=B or comma-separated ?category=A,B
        categories = self.request.query_params.getlist('category')
        parsed_categories = []
        for cat in categories:
            if ',' in cat:
                parsed_categories.extend([c.strip() for c in cat.split(',') if c.strip()])
            elif cat.strip():
                parsed_categories.append(cat.strip())

        if parsed_categories:
            queryset = queryset.filter(category__name__in=parsed_categories)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Public products retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )
