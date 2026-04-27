from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from apps.users.serializers import (RegisterSerializer, UserProfileSerializer, LoginSerializer, 
        ResendVerificationSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
        ChangePasswordSerializer)
from .services import AuthService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from apps.users.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken as RefreshTokenObj
from .tokens import verify_verification_token, verify_password_reset_token
from django.core.cache import cache
from .tasks import send_verification_email, send_password_reset_email
from .google_client import exchange_code_for_tokens, get_google_auth_url, get_user_info

User = get_user_model()
auth_service = AuthService()

class RegisterView(APIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = auth_service.register_user(serializer.validated_data)
            return Response({'detail': 'User registered successfully. Please check your email to verify your account.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'Token is missing, expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = verify_verification_token(token)
            user.is_verified = True 
            user.save()
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Email Verified successfully'}, status=status.HTTP_200_OK)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer
    COOLDOWN_SECONDS = 60

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower().strip()
        cache_key = f"resend_verification_{email}"

        # Cooldown check
        if cache.get(cache_key):
            return Response({"detail": "Please wait before requesting another verification email."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Set cooldown anyway to prevent probing
            cache.set(cache_key, True, timeout=self.COOLDOWN_SECONDS)
            return Response({"detail": "If an account exists, a verification email has been sent."}, status=status.HTTP_200_OK)

        if user.is_verified:
            # Still set cooldown to avoid spam
            cache.set(cache_key, True, timeout=self.COOLDOWN_SECONDS)
            return Response({"detail": "If an account exists, a verification email has been sent."}, status=status.HTTP_200_OK)
        send_verification_email.delay(user.id)
        # Set cooldown
        cache.set(cache_key, True, timeout=self.COOLDOWN_SECONDS)
        return Response({"detail": "If an account exists, a verification email has been sent."}, status=status.HTTP_200_OK)        

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)  
        user = auth_service.login_user(**serializer.validated_data)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return Response({"access": str(access), "refresh": str(refresh)}, status=status.HTTP_200_OK)

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            raise AuthenticationFailed("Refresh token is required")
        try:
            token = RefreshToken(refresh_token)
            token.check_blacklist()
            access_token = str(token.access_token)
            token.blacklist()
            return Response({'new_access': str(access_token), 'new_refresh': str(token)}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Invalid/expired token'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)    
        try:
            token = RefreshToken(refresh)  
            token.blacklist()
        except Exception:
            return Response({'error': 'Failed to blacklist token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
        
class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]       

    def post(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        for outstanding_token in tokens:
            try:
                token = RefreshTokenObj(outstanding_token.token)
                token.blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_204_NO_CONTENT)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        try:
            user = User.objects.get(email=email)
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass  # silent — no enumeration
        return Response(status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        try:
            user = verify_password_reset_token(token)
            user.set_password(new_password)
            user.save()
            tokens = OutstandingToken.objects.filter(user=user)
            for outstanding_token in tokens:
                try:
                    RefreshTokenObj(outstanding_token.token).blacklist()
                except Exception:
                    pass
            return Response(status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]
        user = request.user
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)

class GoogleOAuthRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        url, state = get_google_auth_url()
        return Response({'url': url}, status=status.HTTP_200_OK)
    
class GoogleOAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tokens = exchange_code_for_tokens(code)
            google_user_info = get_user_info(tokens['access_token'])
            user = auth_service.oauth_upsert_user(google_user_info)
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({'access': str(access), 'refresh': str(refresh)}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"OAuth error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        #    return Response({'error': 'Invalid authorization code'}, status=status.HTTP_400_BAD_REQUEST)    

class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user