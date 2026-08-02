from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from admin_settings.models import AuditLog
from admin_settings.serializers import AuditLogSerializer, AuditLogListSerializer

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
