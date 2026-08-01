from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from core.responses import StandardResponse
from .serializers import UserSerializer, UserProfileUpdateSerializer, AdminUserListSerializer

from rest_framework_simplejwt.tokens import RefreshToken

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs) -> StandardResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        data = {
            "id": user.id,
            "email": user.email,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "is_admin": user.is_superuser,
            "is_staff": user.is_staff
        }
        
        return StandardResponse(
            success=True,
            message="User created successfully.",
            data=data,
            status=status.HTTP_201_CREATED
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs) -> StandardResponse:
        response = super().post(request, *args, **kwargs)
        
        # Determine user role
        username = request.data.get('username')
        is_admin = False
        is_staff = False
        try:
            from django.db.models import Q
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            is_admin = user.is_superuser
            is_staff = user.is_staff
        except User.DoesNotExist:
            pass
            
        data = response.data
        data['is_admin'] = is_admin
        data['is_staff'] = is_staff
        
        return StandardResponse(
            success=True,
            message="Login successful.",
            data=data,
            status=status.HTTP_200_OK
        )

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser) # For handling file uploads (avatar) and JSON
    
    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs) -> StandardResponse:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return StandardResponse(
            success=True,
            message="Profile fetched successfully.",
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs) -> StandardResponse:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return StandardResponse(
            success=True,
            message="Profile updated successfully.",
            data=serializer.data,
            status=status.HTTP_200_OK
        )

class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return StandardResponse(
            success=True,
            message="Users retrieved successfully.",
            data=response.data,
            status=status.HTTP_200_OK
        )

from .models import SavedPaymentMethod
from .serializers import SavedPaymentMethodSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

class SavedPaymentMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedPaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedPaymentMethod.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SavedPaymentMethodDetailView(generics.DestroyAPIView):
    serializer_class = SavedPaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedPaymentMethod.objects.filter(user=self.request.user)

class SetDefaultPaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        method = get_object_or_404(SavedPaymentMethod, pk=pk, user=request.user)
        method.is_default = True
        method.save()
        return Response({'status': 'default payment method updated'}, status=status.HTTP_200_OK)

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs) -> StandardResponse:
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(current_password):
            return StandardResponse(
                success=False,
                message="Current password is incorrect.",
                errors={"current_password": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_password or len(new_password) < 6:
            return StandardResponse(
                success=False,
                message="New password must be at least 6 characters long.",
                errors={"new_password": "New password must be at least 6 characters long."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return StandardResponse(
                success=False,
                message="New passwords do not match.",
                errors={"confirm_password": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return StandardResponse(
            success=True,
            message="Password updated successfully.",
            data=None,
            status=status.HTTP_200_OK
        )

class UserDashboardSearchView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> StandardResponse:
        query = request.query_params.get('q', '').strip()
        user = request.user
        
        if not query:
            return StandardResponse(
                success=True,
                message="Empty search query",
                data={"query": "", "total_count": 0, "results": {"orders": [], "payments": [], "wishlist": [], "products": []}},
                status=status.HTTP_200_OK
            )

        from django.db.models import Q
        from orders.models import Order
        from products.models import Product
        from user_activity.models import WishlistItem

        # 1. Search User Orders
        orders = Order.objects.filter(
            user=user
        ).filter(
            Q(order_number__icontains=query) | Q(status__icontains=query) | Q(items__product__name__icontains=query)
        ).distinct()[:5]

        orders_data = [{
            "id": o.id,
            "title": f"Order #{o.order_number}",
            "subtitle": f"৳{o.grand_total:.2f} • {o.get_status_display()}",
            "tab": "orders",
            "badge": o.status,
            "badge_color": "bg-[#5846e0]/10 text-[#5846e0]"
        } for o in orders]

        # 2. Search Saved Payment Methods
        payments = SavedPaymentMethod.objects.filter(
            user=user
        ).filter(
            Q(provider__icontains=query) | Q(account_number__icontains=query)
        )[:5]

        payments_data = [{
            "id": p.id,
            "title": f"{p.get_provider_display()} ({p.account_number})",
            "subtitle": "Default Payment Method" if p.is_default else "Saved Payment Method",
            "tab": "payments",
            "badge": p.provider.upper(),
            "badge_color": "bg-[#5846e0]/10 text-[#5846e0]"
        } for p in payments]

        # 3. Search Wishlist
        wishlist_items = WishlistItem.objects.filter(
            user=user
        ).filter(
            Q(product__name__icontains=query) | Q(product__category__name__icontains=query)
        )[:5]

        wishlist_data = [{
            "id": w.product.id,
            "title": w.product.name,
            "subtitle": f"৳{w.product.price} • Saved in Wishlist",
            "tab": "wishlist",
            "badge": "WISHLIST",
            "badge_color": "bg-pink-100 text-pink-700"
        } for w in wishlist_items]

        # 4. Search Product Catalog
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(description__icontains=query)
        )[:5]

        products_data = [{
            "id": pr.id,
            "title": pr.name,
            "subtitle": f"৳{pr.price} • SKU: {pr.sku or 'N/A'}",
            "tab": "products",
            "badge": "CATALOG",
            "badge_color": "bg-blue-100 text-blue-700"
        } for pr in products]

        total_count = len(orders_data) + len(payments_data) + len(wishlist_data) + len(products_data)

        return StandardResponse(
            success=True,
            message="Search completed.",
            data={
                "query": query,
                "total_count": total_count,
                "results": {
                    "orders": orders_data,
                    "payments": payments_data,
                    "wishlist": wishlist_data,
                    "products": products_data
                }
            },
            status=status.HTTP_200_OK
        )

