from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from products.models import Category
from products.serializers import CategorySerializer
from core.responses import StandardResponse

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Categories retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )
        
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Category created successfully.",
            data=response.data,
            status=status.HTTP_201_CREATED
        )
