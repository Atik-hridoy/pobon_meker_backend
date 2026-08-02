from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from orders.models import Order
from products.models import Product

class AdminOrderListView(ListAPIView):
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related('items__product').all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        search_query = self.request.query_params.get('search')
        
        if status_filter and status_filter.lower() != 'all':
            queryset = queryset.filter(status__iexact=status_filter)
            
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        from orders.serializers import OrderSerializer
        self.serializer_class = OrderSerializer
        response = super().list(request, *args, **kwargs)
        from core.responses import StandardResponse
        return StandardResponse(
            success=True,
            message="Admin orders retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

class AdminOrderDetailUpdateView(RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    queryset = Order.objects.all()
    
    def get_serializer_class(self):
        from orders.serializers import OrderSerializer
        return OrderSerializer
        
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        from core.responses import StandardResponse
        return StandardResponse(
            success=True,
            message="Order details retrieved.",
            data=response.data,
            status=status.HTTP_200_OK
        )
        
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        from core.responses import StandardResponse
        return StandardResponse(
            success=True,
            message="Order updated successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        # If order was cancelled, restore stock
        if old_status != 'CANCELLED' and new_status == 'CANCELLED':
            product_ids = instance.items.values_list('product_id', flat=True)
            products = Product.objects.select_for_update().filter(id__in=product_ids)
            product_map = {p.id: p for p in products}
            
            products_to_update = []
            for item in instance.items.all():
                if item.product_id in product_map:
                    product = product_map[item.product_id]
                    product.stock_count += item.quantity
                    products_to_update.append(product)
            
            if products_to_update:
                Product.objects.bulk_update(products_to_update, ['stock_count'])
                
        # If order is un-cancelled, deduct stock again
        elif old_status == 'CANCELLED' and new_status != 'CANCELLED':
            product_ids = instance.items.values_list('product_id', flat=True)
            products = Product.objects.select_for_update().filter(id__in=product_ids)
            product_map = {p.id: p for p in products}
            
            products_to_update = []
            from rest_framework.exceptions import ValidationError
            for item in instance.items.all():
                if item.product_id in product_map:
                    product = product_map[item.product_id]
                    if product.stock_count < item.quantity:
                        raise ValidationError({'status': f'Cannot un-cancel order. Insufficient stock for "{product.name}".'})
                    product.stock_count -= item.quantity
                    products_to_update.append(product)
            
            if products_to_update:
                Product.objects.bulk_update(products_to_update, ['stock_count'])
                
        serializer.save()
