from rest_framework import generics, status
from rest_framework.response import Response
from products.models import Product, ProductReview
from products.serializers import ProductReviewSerializer
from core.responses import StandardResponse

class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            from rest_framework.permissions import AllowAny
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
