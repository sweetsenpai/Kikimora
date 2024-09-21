from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Discount, LimitTimeProduct
from django.utils import timezone

@shared_task
def new_admin_mail(password, email):
    send_mail('Готов вкалывать?',
                          f'Привет новый ра..сотрудник!\n'
                          f'Для входа в систему тебе нужен логин и пароль.\n'
                          f'Пароль я дам:  {password}  , логин я не дам... \n'
                          f'Логин это твоя почта она у тебя и так есть.\n'
                          f'Только прошу, не давай пароль никому кроме себя, а то всем придется не сладко, особенно тебе!',
                          'settings.EMAIL_HOST_USER',
                          [email],
                          fail_silently=False)


@shared_task
def deactivate_expired_discounts():
    now = timezone.now()
    Discount.objects.filter(end__lte=now, active=True).update(active=False)


@shared_task
def delete_limite_time_product(limittimeproduct_id):
    try:
        day_product = LimitTimeProduct.objects.get(pk=limittimeproduct_id)
        day_product.delete()
        return f'Товар дня id:{limittimeproduct_id} успешно удален.'
    except LimitTimeProduct.DoesNotExist:
        return f'Товар дня id:{limittimeproduct_id} не существует в БД.'