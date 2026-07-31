from django.urls import path
from .views import PlaceOrderView, UserOrdersView

urlpatterns = [
    path('place/', PlaceOrderView.as_view(), name='place-order'),
    path('my-orders/', UserOrdersView.as_view(), name='my-orders'),
]
