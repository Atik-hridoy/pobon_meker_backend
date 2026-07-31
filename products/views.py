from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Category, Product, ProductImage, Banner
from .serializers import CategorySerializer, ProductSerializer, BannerSerializer
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
