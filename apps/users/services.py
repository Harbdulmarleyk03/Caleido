from .models import User, OAuthProvider 
from .tasks import send_verification_email
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from .google_client import get_user_info
from django.db import transaction

class AuthService:
    def __init__(self):
        self.user_model = User

    def register_user(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = self.user_model.objects.create_user(password=password, is_active=True, is_verified=False, **validated_data)
        send_verification_email.delay(str(user.id))        
        return user
    
    def login_user(self, email, password):
        user = authenticate(username=email, password=password)
        if user is None:
            raise AuthenticationFailed("Invalid credentials")  
        if not user.is_verified:
            raise PermissionDenied("Please verify your email")  
        return user
        
    def oauth_upsert_user(self, google_user_info):
        email = google_user_info["email"]
        first_name = google_user_info.get("given_name", "")
        last_name = google_user_info.get("family_name", "")
        provider_uid = google_user_info["sub"]

        with transaction.atomic():
            # 1. Check if this Google account is already linked
            social = OAuthProvider.objects.filter(provider="google", provider_uid=provider_uid).select_related("user").first()
            if social:
                return social.user
            # 2. Check if a user with this email exists
            user = User.objects.filter(email=email).first()
            if user:
                # Link Google account to existing user
                OAuthProvider.objects.create(user=user, provider="google", provider_uid=provider_uid, access_token_enc="", refresh_token_enc="")
                return user
            # 3. Create new user
            username = email.split("@")[0]
            user = User.objects.create(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_verified=True,  # since Google verified it
            )
            user.set_unusable_password()
            user.save()
            # 4. Link Google account
            OAuthProvider.objects.create(user=user, provider="google", provider_uid=provider_uid)
            return user
