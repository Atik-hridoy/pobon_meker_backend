from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.core.cache import cache

from .models import SystemSettings, AuditLog
from .serializers import BillingSettingsSerializer, AuditLogSerializer, AuditLogListSerializer
from .services import create_audit_log

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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


class AuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AuditLogPagination

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        module = self.request.query_params.get('module', None)
        search = self.request.query_params.get('search', None)

        if module:
            queryset = queryset.filter(module__iexact=module)
        if search:
            queryset = queryset.filter(
                Q(user_email__icontains=search) | Q(ip_address__icontains=search)
            )
        
        return queryset


class AuditLogDetailView(generics.RetrieveAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

from .models import Voucher
from .serializers import VoucherSerializer

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
