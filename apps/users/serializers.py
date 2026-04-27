from rest_framework import serializers
from common.serializers import TimezoneField
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, label='Password', write_only=True, required=True)
    password2 = serializers.CharField(min_length=8, label='Confirm Password', write_only=True, required=True)
    timezone = TimezoneField()

    class Meta:
        model = User 
        fields = ['id', 'email', 'password', 'password2', 'first_name', 'last_name', 'username', 'timezone']
        extra_kwargs = {'password2': {'write_only': True}, 
                        'password':  {'write_only': True}}
        read_only_fields = ['id']
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()  

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value.lower()

    def validate_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError('Password must contain at least one number.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match!!!")
        return attrs 

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        user = User.objects.create_user(password=password, **validated_data)
        return user 
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100, required=True)
    password = serializers.CharField(min_length=8, write_only=True, style={'input_type': 'password'})
        
class UserProfileSerializer(serializers.ModelSerializer):
    timezone = TimezoneField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'username', 'timezone', 'locale', 'avatar_url',
            'is_verified', 'date_joined',]
        read_only_fields = [ 'id', 'email', 'is_verified', 'date_joined', 'full_name',]

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'},)
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'},)

    def validate_old_password(self, value):
        """Confirm old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate_new_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError('Password must contain at least one number.')
        return value
    
    def validate(self, data):
        """Cross-field: new password must differ from old."""
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError('New password must be different from your current password.')
        return data

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError('Password must contain at least one number.')
        return value