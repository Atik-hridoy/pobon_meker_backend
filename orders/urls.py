from django.urls import path
from .views import PlaceOrderView, UserOrdersView, PublicActiveVouchersView, AdminOrderListView, AdminOrderDetailUpdateView

urlpatterns = [
    path('place/', PlaceOrderView.as_view(), name='place-order'),
    path('my-orders/', UserOrdersView.as_view(), name='my-orders'),
    path('active-vouchers/', PublicActiveVouchersView.as_view(), name='active-vouchers'),
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', AdminOrderDetailUpdateView.as_view(), name='admin-order-detail'),
]
