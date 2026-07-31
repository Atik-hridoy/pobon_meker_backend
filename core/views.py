from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from admin_settings.models import SystemSettings, Voucher, VoucherUsage
from django.utils import timezone

class CheckoutCalculateView(APIView):
    # Depending on requirements, this might need IsAuthenticated, but checkout might be public.
    # Allowing Any for public checkout calculation
    permission_classes = [] 

    def post(self, request):
        data = request.data
        cart_items = data.get('cart_items', data.get('cartItems', [])) # support both formats
        payment_method = data.get('payment_method', data.get('paymentMethod', 'COD')).upper()
        voucher_code = data.get('voucher_code', None)

        if not isinstance(cart_items, list):
            return Response({'error': 'cart_items must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate subtotal
        subtotal = 0.0
        for item in cart_items:
            try:
                price = float(item.get('price', 0))
                qty = int(item.get('quantity', 1))
                subtotal += price * qty
            except (ValueError, TypeError):
                continue
        
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
        
        if voucher_code:
            now = timezone.now()
            try:
                voucher = Voucher.objects.get(code__iexact=voucher_code)
                
                if not voucher.is_active:
                    return Response({"error": "Invalid or inactive voucher"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if voucher.expiry_date and now > voucher.expiry_date:
                    return Response({"error": "Voucher has expired"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if subtotal < voucher.min_order_amount:
                    return Response({"error": "Minimum order amount not met"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if voucher.usage_limit_total and voucher.used_count >= voucher.usage_limit_total:
                    return Response({"error": "Voucher usage limit reached"}, status=status.HTTP_400_BAD_REQUEST)
                    
                # User Usage Limit Check
                if request.user.is_authenticated:
                    user_usage = VoucherUsage.objects.filter(user=request.user, voucher=voucher).count()
                    if user_usage >= voucher.usage_limit_per_user:
                        return Response({"error": f"You have reached the usage limit for this voucher"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate Discount
                if voucher.discount_type == 'FLAT':
                    discount_amount = voucher.discount_amount
                elif voucher.discount_type == 'PERCENTAGE':
                    calculated_discount = subtotal * (voucher.discount_amount / 100.0)
                    if voucher.max_discount_amount and voucher.max_discount_amount > 0:
                        calculated_discount = min(calculated_discount, voucher.max_discount_amount)
                    discount_amount = calculated_discount
                    
                # Ensure discount_applied never exceeds cart_subtotal
                discount_amount = min(discount_amount, subtotal)
                    
                applied_voucher = {
                    "code": voucher.code,
                    "discount": round(discount_amount, 2)
                }
            except Voucher.DoesNotExist:
                return Response({"error": "Invalid or inactive voucher"}, status=status.HTTP_400_BAD_REQUEST)
                
        taxable_subtotal = max(0.0, subtotal - discount_amount)
        
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
            
        gateway_fee_amount = (taxable_subtotal + vat + delivery) * (fee_pct / 100.0)
            
        # Grand Total
        grand_total = taxable_subtotal + vat + delivery + gateway_fee_amount
        
        response_data = {
            'subtotal': round(subtotal, 2),
            'discount_amount': round(discount_amount, 2),
            'taxable_subtotal': round(taxable_subtotal, 2),
            'vat_amount': round(vat, 2),
            'delivery_charge': round(delivery, 2),
            'gateway_charge': round(gateway_fee_amount, 2),
            'grand_total': round(grand_total, 2),
            'payment_method': payment_method
        }
        
        if applied_voucher:
            response_data['applied_voucher'] = applied_voucher
            
        return Response(response_data)
