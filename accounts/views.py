from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from core.responses import StandardResponse
from .serializers import UserSerializer

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
            user = User.objects.get(username=username)
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
