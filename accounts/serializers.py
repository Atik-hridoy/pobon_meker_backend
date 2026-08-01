from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    re_type_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    phonenumber = serializers.CharField(write_only=True, required=False, allow_blank=True)
    agreed_terms = serializers.BooleanField(write_only=True, required=False, default=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phonenumber', 'password', 're_type_password', 'agreed_terms')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, data):
        # Validate password length
        if len(data.get('password')) < 6:
            raise serializers.ValidationError({"password": "Password must be at least 6 characters long."})
        
        # Validate passwords match
        if data.get('password') != data.get('re_type_password'):
            raise serializers.ValidationError({"re_type_password": "Passwords do not match."})
            
        # Check if email is already taken
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
            
        return data

    def create(self, validated_data):
        # We use email as the username
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data['full_name'].strip()
        phonenumber = validated_data.get('phonenumber', '')
        agreed_terms = validated_data.get('agreed_terms', True)
        
        # Split full_name into first_name and last_name (if possible)
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update user profile created by signal
        user.profile.agreed_terms = bool(agreed_terms)
        if agreed_terms:
            user.profile.agreed_terms_at = timezone.now()
        if phonenumber:
            user.profile.phone_number = phonenumber
        user.profile.save()
        
        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='profile.phone_number', required=False, allow_blank=True)
    shipping_address = serializers.CharField(source='profile.shipping_address', required=False, allow_blank=True)
    avatar = serializers.ImageField(source='profile.avatar', required=False, allow_null=True)
    agreed_terms = serializers.BooleanField(source='profile.agreed_terms', read_only=True)
    agreed_terms_at = serializers.DateTimeField(source='profile.agreed_terms_at', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'shipping_address', 'avatar', 'agreed_terms', 'agreed_terms_at', 'date_joined')
        read_only_fields = ('id', 'email', 'agreed_terms', 'agreed_terms_at', 'date_joined')
        
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update User instance
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        # Update UserProfile instance
        profile = instance.profile
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        
        if 'shipping_address' in profile_data:
            profile.shipping_address = profile_data.get('shipping_address', profile.shipping_address)
        
        # Handle avatar separately (only update if provided)
        if 'avatar' in profile_data:
            profile.avatar = profile_data['avatar']
            
        profile.save()
        
        return instance

class AdminUserListSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='profile.avatar', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    shipping_address = serializers.CharField(source='profile.shipping_address', read_only=True)
    agreed_terms = serializers.BooleanField(source='profile.agreed_terms', read_only=True)
    agreed_terms_at = serializers.DateTimeField(source='profile.agreed_terms_at', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'avatar', 'phone_number', 'shipping_address', 'agreed_terms', 'agreed_terms_at')

from .models import SavedPaymentMethod

class SavedPaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPaymentMethod
        fields = ('id', 'provider', 'account_number', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
