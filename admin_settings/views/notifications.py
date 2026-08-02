from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

class AdminNotificationsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        notifications = []

        try:
            from orders.models import Order
            from products.models import Product
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # 1. Pending Orders Alert
            pending_count = Order.objects.filter(status='PENDING').count()
            if pending_count > 0:
                notifications.append({
                    "id": "notif_pending_orders",
                    "title": "Pending Orders Alert",
                    "message": f"{pending_count} pending order(s) awaiting review and processing.",
                    "time": "Action Required",
                    "type": "warning",
                    "icon": "shopping_bag",
                    "targetTab": "orders"
                })

            # 2. Low Stock Alerts
            low_stock_qs = Product.objects.filter(stock_count__lte=5).order_by('stock_count')[:5]
            for p in low_stock_qs:
                notifications.append({
                    "id": f"notif_low_stock_{p.id}",
                    "title": "Low Stock Warning",
                    "message": f'"{p.name}" has only {p.stock_count} unit(s) left in inventory.',
                    "time": "Inventory Warning",
                    "type": "danger",
                    "icon": "inventory_2",
                    "targetTab": "inventory"
                })

            # 3. New Customer Signups Today
            new_users_count = User.objects.filter(date_joined__gte=today_start).count()
            if new_users_count > 0:
                notifications.append({
                    "id": "notif_new_users",
                    "title": "New Account Signups",
                    "message": f"{new_users_count} new customer(s) registered today.",
                    "time": "Today",
                    "type": "info",
                    "icon": "person_add",
                    "targetTab": "users"
                })

            # 4. Recent Orders
            recent_orders = Order.objects.all().order_by('-created_at')[:4]
            for ord_obj in recent_orders:
                cust_name = ord_obj.full_name or (ord_obj.user.email.split('@')[0] if ord_obj.user and ord_obj.user.email else 'Guest Customer')
                notifications.append({
                    "id": f"notif_order_{ord_obj.id}",
                    "title": f"New Order #{ord_obj.id}",
                    "message": f"{cust_name} placed an order of ৳{float(ord_obj.grand_total):,} ({ord_obj.status})",
                    "time": ord_obj.created_at.strftime('%Y-%m-%d %H:%M'),
                    "type": "success",
                    "icon": "receipt_long",
                    "targetTab": "orders"
                })

        except Exception as e:
            print("Admin Notifications fetch error:", e)

        return Response({
            "notifications": notifications,
            "unread_count": len(notifications),
            "generated_at": now.strftime('%Y-%m-%d %H:%M:%S')
        }, status=status.HTTP_200_OK)
