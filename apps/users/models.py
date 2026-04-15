from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    timezone = models.CharField(max_length=50, default="UTC")
    locale = models.CharField(max_length=10, default="en")
    avatar_url = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email


class OAuthProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="oauth_providers", db_index=True)
    provider = models.CharField(max_length=30)           # e.g. 'google'
    provider_uid = models.CharField(max_length=255)
    access_token_enc = models.TextField()
    refresh_token_enc = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_oauth_provider"

    def __str__(self):
        return f"{self.provider} — {self.user.email}"


class OutstandingToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outstanding_tokens", db_index=True)
    jti = models.CharField(max_length=255, unique=True)  # JWT ID claim
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "users_outstanding_token"

    def __str__(self):
        return f"Token {self.jti} — {self.user.email}"


class BlacklistedToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.OneToOneField(OutstandingToken, on_delete=models.CASCADE, related_name="blacklisted")
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_blacklisted_token"

    def __str__(self):
        return f"Blacklisted {self.token.jti}"