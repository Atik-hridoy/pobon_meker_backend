from rest_framework import serializers
from .models import SystemSettings, AuditLog

class BillingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['vat_enabled', 'vat_percentage', 'delivery_charges', 'gateway_fees', 'updated_at']
        read_only_fields = ['updated_at']

    def validate_vat_percentage(self, value):
        if value < 0:
            raise serializers.ValidationError("VAT percentage cannot be negative.")
        return value

    def validate_delivery_charges(self, value):
        # Expected structure: {"flat_regular": 120.0}
        for charge_type, amount in value.items():
            try:
                amt = float(amount)
                if amt < 0:
                    raise serializers.ValidationError(f"Delivery charge for {charge_type} cannot be negative.")
            except ValueError:
                raise serializers.ValidationError(f"Invalid delivery charge value for {charge_type}.")
        return value

    def validate_gateway_fees(self, value):
        # Expected structure: {"bkash_percentage": 1.5, "nagad_percentage": 1.0, "cod_fee": 0.0}
        for gateway, fee in value.items():
            try:
                amt = float(fee)
                if amt < 0:
                    raise serializers.ValidationError(f"Gateway fee for {gateway} cannot be negative.")
            except ValueError:
                raise serializers.ValidationError(f"Invalid gateway fee value for {gateway}.")
        return value

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        
class AuditLogListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user_email', 'module', 'action', 'ip_address', 'created_at']

from django.utils import timezone
from .models import Voucher

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'
        read_only_fields = ['used_count', 'created_by', 'created_at', 'updated_at']

    def validate_code(self, value):
        code = value.upper()
        if self.instance is None and Voucher.objects.filter(code__iexact=code).exists():
            raise serializers.ValidationError("Voucher code already exists.")
        return code

    def validate_discount_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Discount amount must be positive.")
        return value

    def validate_min_order_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Minimum order amount cannot be negative.")
        return value

    def validate_expiry_date(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value
