from django.urls import path
from .views import CheckoutCalculateView

urlpatterns = [
    path('calculate/', CheckoutCalculateView.as_view(), name='checkout-calculate'),
]
