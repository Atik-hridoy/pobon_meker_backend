from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    re_type_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    phonenumber = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phonenumber', 'password', 're_type_password')
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
        
        # Create user profile
        UserProfile.objects.create(user=user, phone_number=phonenumber)
        
        return user
