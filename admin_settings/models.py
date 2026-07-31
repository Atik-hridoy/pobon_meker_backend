from django.db import models
from django.conf import settings

class SystemSettings(models.Model):
    # This acts like a singleton model where we use the pk=1 or setting_type='billing_and_charges'
    # For now, let's just make it a single row, or type-based.
    setting_type = models.CharField(max_length=50, unique=True, default='billing_and_charges')
    
    # vat_config
    vat_enabled = models.BooleanField(default=True)
    vat_percentage = models.FloatField(default=0.0)
    
    # JSON Fields for nested data
    delivery_charges = models.JSONField(default=dict)
    gateway_fees = models.JSONField(default=dict)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"SystemSettings ({self.setting_type})"

class AuditLog(models.Model):
    user_id = models.IntegerField(null=True, blank=True)
    user_email = models.EmailField(null=True, blank=True)
    module = models.CharField(max_length=100)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    summary = models.JSONField(default=list) # e.g. ["VAT increased by +2.5%"]
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.module} - {self.action} by {self.user_email}"

    def save(self, *args, **kwargs):
        # Prevent updates to audit logs, making them immutable.
        if self.pk is not None:
            raise ValueError("AuditLogs are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLogs are immutable and cannot be deleted.")

from django.utils import timezone

class Voucher(models.Model):
    DISCOUNT_TYPES = (
        ('FLAT', 'Flat Discount'),
        ('PERCENTAGE', 'Percentage Discount'),
    )
    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_amount = models.FloatField()
    max_discount_amount = models.FloatField(null=True, blank=True)
    min_order_amount = models.FloatField(default=0.0)
    usage_limit_per_user = models.IntegerField(default=1)
    usage_limit_total = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

class VoucherUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voucher_usages')
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='usages')
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.user.email if hasattr(self.user, 'email') else self.user} used {self.voucher.code}"
