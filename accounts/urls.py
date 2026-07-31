from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, CustomTokenObtainPairView, ProfileAPIView, AdminUserListView, SavedPaymentMethodListCreateView, SavedPaymentMethodDetailView, SetDefaultPaymentMethodView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileAPIView.as_view(), name='profile-api'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('payment-methods/', SavedPaymentMethodListCreateView.as_view(), name='payment-methods-list'),
    path('payment-methods/<int:pk>/', SavedPaymentMethodDetailView.as_view(), name='payment-methods-detail'),
    path('payment-methods/<int:pk>/set-default/', SetDefaultPaymentMethodView.as_view(), name='payment-methods-default'),
]
