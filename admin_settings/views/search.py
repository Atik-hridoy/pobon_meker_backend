from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

class GlobalSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({
                "query": "",
                "results": {
                    "products": [],
                    "orders": [],
                    "users": [],
                    "vouchers": [],
                    "audit_logs": []
                },
                "total_count": 0
            }, status=status.HTTP_200_OK)

        from orders.models import Order
        from products.models import Product
        from django.contrib.auth import get_user_model
        from admin_settings.models import Voucher, AuditLog
        User = get_user_model()

        products_list = []
        orders_list = []
        users_list = []
        vouchers_list = []
        audit_logs_list = []

        try:
            # 1. Search Products (Inventory)
            product_qs = Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(sku__icontains=query)
            ).distinct()[:6]

            for p in product_qs:
                products_list.append({
                    "id": p.id,
                    "title": p.name,
                    "subtitle": f"Category: {p.category.name if p.category else 'Uncategorized'} | Stock: {p.stock_count} | Price: ৳{p.price}",
                    "tab": "inventory",
                    "badge": "Product",
                    "badge_color": "bg-blue-100 text-blue-800"
                })

            # 2. Search Orders
            order_q_filter = Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(status__icontains=query) | Q(user__email__icontains=query)
            if query.isdigit():
                order_q_filter |= Q(id=int(query))
            elif query.lower().startswith('order #') or query.lower().startswith('#'):
                clean_num = query.replace('Order #', '').replace('#', '').strip()
                if clean_num.isdigit():
                    order_q_filter |= Q(id=int(clean_num))

            order_qs = Order.objects.filter(order_q_filter).distinct()[:6]

            for ord_obj in order_qs:
                cust_name = ord_obj.full_name or (ord_obj.user.email if ord_obj.user else 'Guest')
                orders_list.append({
                    "id": ord_obj.id,
                    "title": f"Order #{ord_obj.id} - {cust_name}",
                    "subtitle": f"Amount: ৳{float(ord_obj.grand_total):,} | Status: {ord_obj.status} | Date: {ord_obj.created_at.strftime('%Y-%m-%d')}",
                    "tab": "orders",
                    "badge": "Order",
                    "badge_color": "bg-green-100 text-green-800"
                })

            # 3. Search Users
            user_qs = User.objects.filter(
                Q(email__icontains=query) |
                Q(full_name__icontains=query) |
                Q(phone_number__icontains=query)
            ).distinct()[:6]

            for u in user_qs:
                users_list.append({
                    "id": u.id,
                    "title": getattr(u, 'full_name', '') or u.email,
                    "subtitle": f"Email: {u.email} | Role: {'Admin' if u.is_staff or u.is_superuser else 'Customer'}",
                    "tab": "users",
                    "badge": "User",
                    "badge_color": "bg-purple-100 text-purple-800"
                })

            # 4. Search Vouchers
            voucher_qs = Voucher.objects.filter(
                Q(code__icontains=query)
            )[:5]

            for v in voucher_qs:
                vouchers_list.append({
                    "id": v.id,
                    "title": f"Voucher: {v.code}",
                    "subtitle": f"Type: {v.discount_type} | Discount: {v.discount_amount} | Active: {'Yes' if v.is_active else 'No'}",
                    "tab": "billing",
                    "badge": "Voucher",
                    "badge_color": "bg-amber-100 text-amber-800"
                })

            # 5. Search Audit Logs
            audit_qs = AuditLog.objects.filter(
                Q(module__icontains=query) |
                Q(action__icontains=query) |
                Q(user_email__icontains=query) |
                Q(ip_address__icontains=query)
            )[:5]

            for a in audit_qs:
                audit_logs_list.append({
                    "id": a.id,
                    "title": f"{a.module} - {a.action}",
                    "subtitle": f"By: {a.user_email or 'System'} | IP: {a.ip_address} | Time: {a.created_at.strftime('%Y-%m-%d %H:%M')}",
                    "tab": "audit",
                    "badge": "Audit Log",
                    "badge_color": "bg-slate-100 text-slate-800"
                })

        except Exception as e:
            print("Global search exception:", e)

        total_count = len(products_list) + len(orders_list) + len(users_list) + len(vouchers_list) + len(audit_logs_list)

        return Response({
            "query": query,
            "results": {
                "products": products_list,
                "orders": orders_list,
                "users": users_list,
                "vouchers": vouchers_list,
                "audit_logs": audit_logs_list
            },
            "total_count": total_count
        }, status=status.HTTP_200_OK)
