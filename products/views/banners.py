from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from products.models import Banner
from products.serializers import BannerSerializer
from core.responses import StandardResponse

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
