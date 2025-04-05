from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import os
from dotenv import load_dotenv
import logging
from shop.services.email_verification import generate_email_token
load_dotenv()
logger = logging.getLogger(__name__)


@shared_task
def send_confirmation_email(user):
    token = generate_email_token(user.get(user_id))
    verification_url = f"{os.getenv('MAIN_DOMAIN')}api/v1/verify-email/{token}/"

    # Рендеринг HTML-шаблона
    html_content = render_to_string('emails/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
    })

    # Создаем сообщение
    email_message = EmailMessage(
        subject='Подтверждение email',
        body=html_content,
        from_email=os.getenv("EMAIL"),
        to=[user.email],
    )
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)

