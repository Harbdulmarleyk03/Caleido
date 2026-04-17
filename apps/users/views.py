from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from apps.users.serializers import RegisterSerializer, UserProfileSerializer, LoginSerializer
from .services import AuthService
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

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
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

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


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user