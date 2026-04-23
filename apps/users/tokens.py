from django.core import signing
from .models import User 

def generate_verification_token(user):
    signed_token = signing.dumps({'user_id': str(user.id)}, salt='email-verification')
    return signed_token

def verify_verification_token(token, max_age=86400):
    try:
        data = signing.loads(token, salt='email-verification', max_age=max_age)
        user = User.objects.get(id=data['user_id'])
        return user 
    except signing.SignatureExpired:
        raise ValueError("Token Expired")
    except signing.BadSignature:
        raise ValueError("Token Tampered") 

def generate_password_reset_token(user):
    signed_token = signing.dumps({'user_id': str(user.id)}, salt='password-reset')
    return signed_token

def verify_password_reset_token(token, max_age=3600):
    try:
        data = signing.loads(token, salt='password-reset', max_age=max_age)
        user = User.objects.get(id=data['user_id'])
        return user 
    except signing.SignatureExpired:
        raise ValueError("Token Expired")
    except signing.BadSignature:
        raise ValueError("Token Tampered") 
