from django.contrib import admin
from .models import SystemSettings, AuditLog, Voucher, VoucherUsage

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['setting_type', 'vat_enabled', 'vat_percentage', 'updated_at']
    readonly_fields = ['updated_at']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['module', 'action', 'user_email', 'ip_address', 'created_at']
    search_fields = ['module', 'action', 'user_email', 'ip_address']
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_amount', 'is_active', 'expiry_date', 'used_count']
    search_fields = ['code']
    list_filter = ['discount_type', 'is_active']

@admin.register(VoucherUsage)
class VoucherUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'voucher', 'used_at']
    search_fields = ['user__email', 'voucher__code']
