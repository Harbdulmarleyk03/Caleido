from django.core import signing
from .models import User 

def generate_verification_token(user):
    signed_token = signing.dumps({'user_id': '123'}, salt='email-verification')
    return signed_token

def verify_verification_token(token):
    try:
        data = signing.loads(token, salt='email-verification', max_age=86400)
        user = User.objects.get(id=data['uid'])

        if user.email != data['email']:
            raise Exception("Invalid email")
        if user.is_verified != data['verified']:
            raise Exception("Token already used")
        user.is_verified = True
        user.save()
        return user 
    except signing.SignatureExpired:
        raise ValueError("Token Expired")
    except signing.BadSignature:
        raise ValueError("Token Tampered") 

