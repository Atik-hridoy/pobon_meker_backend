from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache

from admin_settings.models import SystemSettings

DEFAULT_TERMS_BD = """1. Orders & Delivery in Bangladesh: Orders within Dhaka City are delivered within 24-48 hours. Outside Dhaka orders are shipped via Courier Services (Steadfast/Sundarban/Pathao) within 2-4 business days.
2. Pricing & Taxes: All product prices are listed in Bangladeshi Taka (৳ BDT) inclusive of applicable taxes under Bangladesh VAT Regulations.
3. Payment Methods: We accept Cash on Delivery (COD), Mobile Financial Services (bKash, Nagad, Rocket), and Debit/Credit Cards.
4. Consumer Rights & Returns: Per Bangladesh Consumer Rights Protection Act, 2009, customers can inspect components upon delivery. Defective or incorrect items reported within 7 days qualify for free replacement or full refund.
5. Cancellation Policy: Orders may be cancelled free of charge prior to courier dispatch."""

DEFAULT_PRIVACY_BD = """1. Data Privacy Standard: We collect customer name, phone number, shipping address, and email solely for order delivery and customer support in Bangladesh.
2. Financial & Account Security: Transactions via bKash, Nagad, or Bank Cards adhere strictly to Bangladesh MFS & Digital Security Regulations. We do not sell or share customer data with third parties.
3. Cookies & Session Storage: Our platform uses essential cookies to preserve shopping cart contents and user session preferences.
4. Customer Rights: Customers can request access, update, or deletion of their registered account info by emailing support@pabonmaker.com or calling +880 1700-000000."""

class StoreConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        settings, _ = SystemSettings.objects.get_or_create(setting_type='store_config')
        data = {
            "site_name": getattr(settings, 'site_name', 'PABON MAKER'),
            "site_tagline": getattr(settings, 'site_tagline', 'Engineering Components & Maker Hub Bangladesh'),
            "currency_symbol": "৳",
            "currency_code": "BDT",
            "timezone": "Asia/Dhaka",
            "country": "Bangladesh",
            "support_phone": getattr(settings, 'support_phone', '+880 1700-000000'),
            "support_email": getattr(settings, 'support_email', 'support@pabonmaker.com'),
            "address": getattr(settings, 'address', 'Dhaka, Bangladesh'),
            "delivery_inside_dhaka": float(getattr(settings, 'delivery_inside_dhaka', 60.00)),
            "delivery_outside_dhaka": float(getattr(settings, 'delivery_outside_dhaka', 120.00)),
            "terms_and_conditions": getattr(settings, 'terms_and_conditions', '') or DEFAULT_TERMS_BD,
            "privacy_policy": getattr(settings, 'privacy_policy', '') or DEFAULT_PRIVACY_BD,
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        settings, _ = SystemSettings.objects.get_or_create(setting_type='store_config')
        data = request.data
        if 'site_name' in data and data['site_name']:
            settings.site_name = data['site_name']
        if 'site_tagline' in data and data['site_tagline']:
            settings.site_tagline = data['site_tagline']
        if 'support_phone' in data:
            settings.support_phone = data['support_phone']
        if 'support_email' in data:
            settings.support_email = data['support_email']
        if 'address' in data:
            settings.address = data['address']
        if 'delivery_inside_dhaka' in data:
            settings.delivery_inside_dhaka = data['delivery_inside_dhaka']
        if 'delivery_outside_dhaka' in data:
            settings.delivery_outside_dhaka = data['delivery_outside_dhaka']
        if 'terms_and_conditions' in data:
            settings.terms_and_conditions = data['terms_and_conditions']
        if 'privacy_policy' in data:
            settings.privacy_policy = data['privacy_policy']
        
        settings.save()
        cache.delete('store_config')

        res_data = {
            "site_name": settings.site_name,
            "site_tagline": settings.site_tagline,
            "currency_symbol": "৳",
            "currency_code": "BDT",
            "timezone": "Asia/Dhaka",
            "country": "Bangladesh",
            "support_phone": settings.support_phone,
            "support_email": settings.support_email,
            "address": settings.address,
            "delivery_inside_dhaka": float(settings.delivery_inside_dhaka),
            "delivery_outside_dhaka": float(settings.delivery_outside_dhaka),
            "terms_and_conditions": settings.terms_and_conditions,
            "privacy_policy": settings.privacy_policy,
        }
        return Response(res_data, status=status.HTTP_200_OK)
