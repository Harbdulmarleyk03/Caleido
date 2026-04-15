from .models import User 
from .tasks import send_verification_email
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

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
        user = authenticate(request=None, username=email, password=password)
        if user and user.is_verified:
            return user, f"User Logged in successfully"
        raise AuthenticationFailed("User is not verified")
    