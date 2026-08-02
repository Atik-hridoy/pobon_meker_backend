from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from admin_settings.models import SystemSettings, Voucher, VoucherUsage
from products.models import Product
from django.db.models import Q
from .models import Order, OrderItem
from django.utils import timezone
from django.db import transaction

class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        cart_items = data.get('cart_items', data.get('cartItems', []))
        payment_method = data.get('payment_method', data.get('paymentMethod', 'COD')).upper()
        voucher_code = data.get('voucher_code', None)
        shipping_info = data.get('shipping_info', {})

        if not isinstance(cart_items, list) or not cart_items:
            return Response({'error': 'cart_items must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract all product IDs to lock them in bulk
        product_ids = [item.get('product_id') for item in cart_items if item.get('product_id')]
        
        if not product_ids:
            return Response({'error': 'No valid products in cart'}, status=status.HTTP_400_BAD_REQUEST)

        # Lock products to prevent race conditions during concurrent checkouts
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        product_map = {p.id: p for p in products}
        
        subtotal = 0.0
        order_items_data = []
        products_to_update = []

        for item in cart_items:
            try:
                product_id = item.get('product_id')
                qty = int(item.get('quantity', 1))
                
                if qty <= 0:
                    return Response({'error': 'Quantity must be at least 1'}, status=status.HTTP_400_BAD_REQUEST)
                
                if product_id not in product_map:
                    return Response({'error': f'Product {product_id} not found or unavailable.'}, status=status.HTTP_400_BAD_REQUEST)
                
                product = product_map[product_id]
                
                # 1. Stock Validation
                if product.stock_count < qty:
                    return Response({'error': f'Insufficient stock for "{product.name}". Only {product.stock_count} left.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 2. Enforce True Price (Ignore frontend price completely)
                price = float(product.price)
                subtotal += price * qty
                
                # 3. Deduct Stock
                product.stock_count -= qty
                products_to_update.append(product)
                
                order_items_data.append({
                    'product': product,
                    'price': price,
                    'quantity': qty
                })
            except (ValueError, TypeError):
                return Response({'error': 'Invalid payload format.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save all stock updates
        Product.objects.bulk_update(products_to_update, ['stock_count'])
        
        # Get billing settings
        settings = cache.get('billing_and_charges')
        if not settings:
            try:
                settings_obj = SystemSettings.objects.get(setting_type='billing_and_charges')
                settings = {
                    'vat_enabled': settings_obj.vat_enabled,
                    'vat_percentage': settings_obj.vat_percentage,
                    'delivery_charges': settings_obj.delivery_charges,
                    'gateway_fees': settings_obj.gateway_fees
                }
                cache.set('billing_and_charges', settings, timeout=86400)
            except SystemSettings.DoesNotExist:
                settings = {
                    'vat_enabled': False,
                    'vat_percentage': 0.0,
                    'delivery_charges': {'flat_regular': 0.0},
                    'gateway_fees': {'bkash_percentage': 0.0, 'nagad_percentage': 0.0, 'cod_fee': 0.0}
                }
                
        # Handle Voucher
        discount_amount = 0.0
        applied_voucher = None
        voucher_obj = None
        
        if voucher_code:
            now = timezone.now()
            try:
                voucher_obj = Voucher.objects.get(code__iexact=voucher_code)
                
                if not voucher_obj.is_active:
                    return Response({"error": "Invalid or inactive voucher"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if voucher_obj.expiry_date and now > voucher_obj.expiry_date:
                    return Response({"error": "Voucher has expired"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if subtotal < voucher_obj.min_order_amount:
                    return Response({"error": "Minimum order amount not met"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if voucher_obj.usage_limit_total and voucher_obj.used_count >= voucher_obj.usage_limit_total:
                    return Response({"error": "Voucher usage limit reached"}, status=status.HTTP_400_BAD_REQUEST)
                    
                # User Usage Limit Check
                if request.user.is_authenticated:
                    user_usage = VoucherUsage.objects.filter(user=request.user, voucher=voucher_obj).count()
                    if user_usage >= voucher_obj.usage_limit_per_user:
                        return Response({"error": f"You have reached the usage limit for this voucher"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate Discount
                if voucher_obj.discount_type == 'FLAT':
                    discount_amount = voucher_obj.discount_amount
                elif voucher_obj.discount_type == 'PERCENTAGE':
                    calculated_discount = subtotal * (float(voucher_obj.discount_amount) / 100.0)
                    if voucher_obj.max_discount_amount and voucher_obj.max_discount_amount > 0:
                        calculated_discount = min(calculated_discount, float(voucher_obj.max_discount_amount))
                    discount_amount = calculated_discount
                    
                # Ensure discount_applied never exceeds cart_subtotal
                discount_amount = float(min(discount_amount, subtotal))
                    
                applied_voucher = voucher_obj.code
            except Voucher.DoesNotExist:
                return Response({"error": "Invalid or inactive voucher"}, status=status.HTTP_400_BAD_REQUEST)
                
        taxable_subtotal = max(0.0, subtotal - float(discount_amount))
        
        # Calculate VAT on taxable subtotal
        vat = 0.0
        if settings.get('vat_enabled'):
            vat_pct = float(settings.get('vat_percentage', 0))
            vat = taxable_subtotal * (vat_pct / 100.0)
            
        # Calculate Delivery
        delivery_charges = settings.get('delivery_charges', {})
        delivery = float(delivery_charges.get('flat_regular', 0))
        
        # Calculate Gateway Fee on (Taxable Subtotal + VAT + Delivery)
        gateway_fees = settings.get('gateway_fees', {})
        gateway_fee_amount = 0.0
        
        fee_pct = 0.0
        if payment_method == 'BKASH':
            fee_pct = float(gateway_fees.get('bkash_percentage', 0))
        elif payment_method == 'NAGAD':
            fee_pct = float(gateway_fees.get('nagad_percentage', 0))
        elif payment_method == 'COD':
            fee_pct = float(gateway_fees.get('cod_fee', 0))
        elif payment_method == 'CARD':
            # Add a default card fee if needed, or 0
            fee_pct = 0.0
            
        gateway_fee_amount = (taxable_subtotal + vat + delivery) * (fee_pct / 100.0)
            
        # Grand Total
        grand_total = taxable_subtotal + vat + delivery + gateway_fee_amount
        
        # Determine Initial Status
        initial_status = 'CONFIRMED' if payment_method in ['BKASH', 'NAGAD'] else 'PENDING'

        # CREATE THE ORDER
        order = Order(
            user=request.user,
            full_name=shipping_info.get('fullName', 'Guest'),
            email=shipping_info.get('email', ''),
            phone=shipping_info.get('phone', ''),
            address=shipping_info.get('address', ''),
            payment_method=payment_method,
            applied_voucher=applied_voucher,
            subtotal=subtotal,
            discount_amount=discount_amount,
            vat_amount=vat,
            delivery_charge=delivery,
            gateway_fee=gateway_fee_amount,
            grand_total=grand_total,
            status=initial_status
        )
        order.save()
        
        # CREATE ORDER ITEMS
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )

        # UPDATE VOUCHER USAGE
        if voucher_obj:
            voucher_obj.used_count += 1
            voucher_obj.save()
            if request.user.is_authenticated:
                VoucherUsage.objects.create(user=request.user, voucher=voucher_obj)

        return Response({
            'message': 'Order placed successfully',
            'order_number': order.order_number,
            'grand_total': round(grand_total, 2)
        }, status=status.HTTP_201_CREATED)

class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .serializers import OrderSerializer
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PublicActiveVouchersView(APIView):
    permission_classes = []
    
    def get(self, request):
        now = timezone.now()
        vouchers = Voucher.objects.filter(is_active=True).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=now)
        ).order_by('-created_at')
        
        # We don't have a public serializer yet, let's just serialize the data manually 
        # or we could use VoucherSerializer if we import it, but let's send what we need
        data = []
        for v in vouchers:
            # check usage limit
            if v.usage_limit_total and v.used_count >= v.usage_limit_total:
                continue
                
            data.append({
                'code': v.code,
                'discount_type': v.discount_type,
                'discount_amount': v.discount_amount,
                'min_order_amount': v.min_order_amount,
                'max_discount_amount': v.max_discount_amount,
                'expiry_date': v.expiry_date
            })
            
        return Response(data, status=status.HTTP_200_OK)

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
        from .serializers import OrderSerializer
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
        from .serializers import OrderSerializer
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
