from celery import shared_task
from django.core.mail import send_mail
import uuid

@shared_task
def send_verification_email(user_id):
    pass