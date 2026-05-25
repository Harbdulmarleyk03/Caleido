from django.core import signing
from apps.bookings.models import Booking

def generate_cancel_token(booking):
    signed_token = signing.dumps({'booking_id': str(booking.id)}, salt='cancel-booking')
    return signed_token

def verify_cancel_token(token, max_age=604800):
    try:
        data = signing.loads(token, salt='cancel-booking', max_age=max_age)
        booking = Booking.objects.get(id=data['booking_id'])
        return booking 
    except signing.SignatureExpired:
        raise ValueError("Token Expired")
    except signing.BadSignature:
        raise ValueError("Token Tampered") 
    except Booking.DoesNotExist:
        raise ValueError("Invalid Booking")