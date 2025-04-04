from celery import shared_task
from django.core.mail import EmailMessage
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


@shared_task
def new_admin_mail(password, email):
    html_content = f"""
    <html>
        <body>
            <h1 style="color: #4CAF50;">Добро пожаловать в команду!</h1>
            <p>Привет, новый <strong>сотрудник</strong>!</p>
            <p>Для входа в систему тебе понадобятся логин и пароль:</p>
            <ul>
                <li><strong>Логин:</strong> {email}</li>
                <li><strong>Пароль:</strong> {password}</li>
            </ul>
            <p>Только прошу, не давай пароль никому, иначе будут проблемы!</p>
        </body>
    </html>
    """

    # Создаем сообщение
    email_message = EmailMessage(
        subject="Готов вкалывать?",
        body=html_content,
        from_email=os.getenv("EMAIL"),
        to=[email],
    )
    try:
        email_message.content_subtype = "html"
        email_message.send(fail_silently=False)
    except Exception as e:
        logger.error(f'Во время отправки письма новому администратору произошла ошибка.\nERROR:{e}')
    return


@shared_task(bind=True, max_retries=3)
def feedback_email(self, feedback_data):
    """
    Отправляет письмо с информацией об обратной связи на вашу почту.

    :param self: Объект задачи Celery.
    :param feedback_data: Словарь с данными формы обратной связи.
                          Пример:
                          {
                              "name": "Иван Иванов",
                              "phone": "+79991234567",
                              "email": "user@example.com",
                              "question": "Как оформить заказ?"
                          }
    """
    try:
        # HTML-содержимое письма
        html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h1 style="color: #4CAF50;">Новое сообщение с формы обратной связи</h1>
                    <p>Получено новое сообщение от пользователя:</p>
                    <ul style="list-style-type: none; padding: 0;">
                        <li><strong>Имя:</strong> {feedback_data.get("name", "Не указано")}</li>
                        <li><strong>Телефон:</strong> {feedback_data.get("phone", "Не указан")}</li>
                        <li><strong>Email:</strong> {feedback_data.get("email", "Не указан")}</li>
                        <li><strong>Сообщение:</strong> {feedback_data.get("question", "Не указано")}</li>
                    </ul>

                    <!-- Подвал -->
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                    <footer style="text-align: center; color: #888; font-size: 14px;">
                        <p>С уважением, команда мастерской "Кикимора"</p>
                        <p>Контакты: 
                            <a href="mailto:{os.getenv("KIKIMORA_EMAIL")}" style="color: #4CAF50; text-decoration: none;">{os.getenv("KIKIMORA_EMAIL")}</a> | 
                            Телефон: <a href="tel:{os.getenv("KIKIMORA_PHONE_RAW")}" style="color: #4CAF50; text-decoration: none;">{os.getenv("KIKIMORA_PHONE")}</a>
                        </p>
                        <p>Адрес: {os.getenv("KIKIMORA_ADDRESS")}</p>
                        <p>Следите за нами: 
                            <a href="{os.getenv("KIKIMORA_VK")}" style="color: #4CAF50; text-decoration: none;">ВКонтакте</a> | 
                            <a href="{os.getenv("KIKIMORA_INSTAGRAM")}" style="color: #4CAF50; text-decoration: none;">Instagram</a>
                        </p>
                    </footer>
                </body>
            </html>
        """

        # Создаем сообщение
        email_message = EmailMessage(
            subject="Новое сообщение с формы обратной связи",
            body=html_content,
            from_email=os.getenv("EMAIL"),
            to=[os.getenv("EMAIL")],  # Ваша почта для получения обратной связи
        )

        # Указываем, что содержимое письма в формате HTML
        email_message.content_subtype = "html"

        # Отправляем письмо
        email_message.send(fail_silently=False)

    except Exception as e:
        logger.error(f"Во время отправки обратной связи произошла непредвиденная ошибка.\nERROR: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)  # Повторная попытка отправки