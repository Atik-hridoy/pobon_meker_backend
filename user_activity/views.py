from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import RecentlyViewed
from products.models import Product
from products.serializers import ProductSerializer

class TrackProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the recently viewed record
        obj, created = RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product
        )
        if not created:
            # update_or_create doesn't trigger auto_now if we just fetch it, so force save to update timestamp
            obj.save()

        # Enforce limit of 12
        recent_ids = RecentlyViewed.objects.filter(user=request.user).order_by('-viewed_at').values_list('id', flat=True)[:12]
        RecentlyViewed.objects.filter(user=request.user).exclude(id__in=recent_ids).delete()

        return Response({'message': 'Product view tracked successfully'}, status=status.HTTP_200_OK)


class MyRecentlyViewedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recent_views = RecentlyViewed.objects.filter(user=request.user).order_by('-viewed_at')
        products = [rv.product for rv in recent_views]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from .models import WishlistItem

class ToggleWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            
        wishlist_item = WishlistItem.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            wishlist_item.delete()
            return Response({'status': 'removed', 'message': 'Removed from wishlist'}, status=status.HTTP_200_OK)
        else:
            WishlistItem.objects.create(user=request.user, product=product)
            return Response({'status': 'added', 'message': 'Added to wishlist'}, status=status.HTTP_200_OK)

class MyWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist_items = WishlistItem.objects.filter(user=request.user).order_by('-added_at')
        products = [item.product for item in wishlist_items]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserRecommendationsView(APIView):
    permission_classes = [] # Handled internally

    def get(self, request):
        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)
            
        recent_views = RecentlyViewed.objects.filter(user=request.user)
        wishlist_items = WishlistItem.objects.filter(user=request.user)
        
        if not recent_views.exists() and not wishlist_items.exists():
            return Response([], status=status.HTTP_200_OK)
            
        category_ids = set()
        product_ids_to_exclude = set()
        
        for rv in recent_views:
            if rv.product.category:
                category_ids.add(rv.product.category.id)
            product_ids_to_exclude.add(rv.product.id)
            
        for wi in wishlist_items:
            if wi.product.category:
                category_ids.add(wi.product.category.id)
            product_ids_to_exclude.add(wi.product.id)
            
        if not category_ids:
            return Response([], status=status.HTTP_200_OK)
            
        # Get products in these categories, exclude already viewed/wishlisted, order by some metric or random
        recommended_products = Product.objects.filter(
            category_id__in=category_ids,
            stock_count__gt=0
        ).exclude(id__in=product_ids_to_exclude).order_by('?')[:8] # '?' for random, or we can use '-created_at'
        
        serializer = ProductSerializer(recommended_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
