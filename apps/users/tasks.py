from celery import shared_task
from django.core.mail import send_mail
from .tokens import generate_verification_token
from .models import User
from django.urls import reverse
from django.conf import settings

@shared_task
def send_verification_email(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return f"User with the id {user_id} does not exist"
    
    token = generate_verification_token(user)

    path = reverse("verify-email")
    verification_url = f"{settings.DOMAIN}{path}?token={token}"

    subject = "Verify your email"
    message = (
        f"Hi {user.first_name or 'there'},\n\n"
        f"Please verify your email by clicking the link below:\n\n"
        f"{verification_url}\n\n"
        f"This link will expire soon.\n\n"
        f"If you didn’t create an account, you can ignore this email."
    )

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )

    return f"Verification email sent to {user.email}"

