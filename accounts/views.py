from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from core.responses import StandardResponse
from .serializers import UserSerializer, UserProfileUpdateSerializer, AdminUserListSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs) -> StandardResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        data = {
            "id": user.id,
            "email": user.email
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

    def patch(self, request, pk):
        method = get_object_or_404(SavedPaymentMethod, pk=pk, user=request.user)
        method.is_default = True
        method.save()
        return Response({'message': 'Default payment method updated.'}, status=status.HTTP_200_OK)
