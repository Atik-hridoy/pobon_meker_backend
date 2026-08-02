from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from admin_settings.models import Voucher

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
