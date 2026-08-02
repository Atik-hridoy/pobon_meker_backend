from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.core.cache import cache

from admin_settings.models import SystemSettings, Voucher
from admin_settings.serializers import BillingSettingsSerializer, VoucherSerializer
from admin_settings.services import create_audit_log
from .utils import get_client_ip

class BillingSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        settings, _ = SystemSettings.objects.get_or_create(setting_type='billing_and_charges')
        serializer = BillingSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        settings, _ = SystemSettings.objects.get_or_create(setting_type='billing_and_charges')
        
        # Serialize old values to compare
        old_serializer = BillingSettingsSerializer(settings)
        old_value = old_serializer.data

        serializer = BillingSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            new_value = serializer.data

            # Create Audit Log
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            create_audit_log(
                user=request.user,
                module='Billing & Charges',
                action='Updated Rates',
                ip_address=ip_address,
                user_agent=user_agent,
                old_value=old_value,
                new_value=new_value
            )
            
            # Invalidate/Update Cache for public checkout
            cache.delete('billing_and_charges')
            cache.set('billing_and_charges', new_value, timeout=86400) # cache for 24h

            return Response(new_value, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VoucherListCreateView(generics.ListCreateAPIView):
    queryset = Voucher.objects.all().order_dict() if hasattr(Voucher.objects.all(), 'order_dict') else Voucher.objects.all().order_by('-created_at')
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        voucher = serializer.save(created_by=self.request.user)
        
        # Create Audit Log
        ip_address = get_client_ip(self.request)
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        create_audit_log(
            user=self.request.user,
            module='Marketing/Vouchers',
            action='CREATE_VOUCHER',
            ip_address=ip_address,
            user_agent=user_agent,
            old_value=None,
            new_value={"code": voucher.code, "discount_type": voucher.discount_type, "discount_amount": voucher.discount_amount}
        )

class VoucherToggleStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            voucher = Voucher.objects.get(pk=pk)
            old_status = voucher.is_active
            voucher.is_active = not voucher.is_active
            voucher.save()
            
            # Create Audit Log
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            create_audit_log(
                user=request.user,
                module='Marketing/Vouchers',
                action='TOGGLE_VOUCHER_STATUS',
                ip_address=ip_address,
                user_agent=user_agent,
                old_value={"is_active": old_status},
                new_value={"is_active": voucher.is_active}
            )
            
            return Response({"is_active": voucher.is_active}, status=status.HTTP_200_OK)
        except Voucher.DoesNotExist:
            return Response({"error": "Voucher not found"}, status=status.HTTP_404_NOT_FOUND)
