from django.urls import path
from .views import BillingSettingsView, AuditLogListView, AuditLogDetailView, VoucherListCreateView, VoucherToggleStatusView, StoreAnalyticsAPIView, DashboardTelemetryAPIView, StoreConfigView, AdminNotificationsAPIView, GlobalSearchAPIView

urlpatterns = [
    path('billing-settings/', BillingSettingsView.as_view(), name='billing-settings'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs-list'),
    path('audit-logs/<int:pk>/', AuditLogDetailView.as_view(), name='audit-logs-detail'),
    path('vouchers/', VoucherListCreateView.as_view(), name='vouchers-list-create'),
    path('vouchers/<int:pk>/toggle-status/', VoucherToggleStatusView.as_view(), name='vouchers-toggle-status'),
    path('analytics/', StoreAnalyticsAPIView.as_view(), name='store-analytics'),
    path('dashboard-telemetry/', DashboardTelemetryAPIView.as_view(), name='dashboard-telemetry'),
    path('store-config/', StoreConfigView.as_view(), name='store-config'),
    path('notifications/', AdminNotificationsAPIView.as_view(), name='admin-notifications'),
    path('global-search/', GlobalSearchAPIView.as_view(), name='global-search'),
]


