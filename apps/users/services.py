from .models import User 
from .tasks import send_verification_email
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

class AuthService:
    def __init__(self):
        self.user_model = User

    def register_user(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = self.user_model.objects.create_user(password=password,is_active=True, is_verified=False, **validated_data)
        send_verification_email.delay(str(user.id))        
        return user
    
    def login_user(self, email, password):
        user = authenticate(username=email, password=password)
        if user is None:
            raise AuthenticationFailed("Invalid credentials")  
        if not user.is_verified:
            raise PermissionDenied("Please verify your email")  
        return user