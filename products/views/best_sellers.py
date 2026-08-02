from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from products.models import Product
from products.serializers import ProductSerializer
from core.responses import StandardResponse

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
