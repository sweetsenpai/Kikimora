from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Discount, LimitTimeProduct, PromoSystem
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
def deactivate_expired_discount(discount_id):
    discount = Discount.objects.filter(discount_id=discount_id).first()
    if not discount:
        return f'Скидки с указаным id:{discount_id} не существует в БД.'
    discount.active = False
    discount.save()
    return f'Скдка с id {discount_id} удалена.'


@shared_task
def activate_discount(discount_id):
    discount = Discount.objects.filter(discount_id=discount_id).first()
    if not discount:
        return f'Скидки с указаным id:{discount_id} не существует в БД.'
    discount.active = True
    discount.save()
    return f'Скдка с id {discount_id} активирована.'


@shared_task
def deactivate_expired_promo(promo_id):
    promo = PromoSystem.objects.filter(promo_id=promo_id).first()
    if not promo:
        return f'Промокод с id {promo_id} не существует в БД.'
    promo.active = False
    promo.save()
    return f'Промокод с id {promo_id} теперь не активен.'


@shared_task
def activate_promo(promo_id):
    promo = PromoSystem.objects.filter(promo_id=promo_id).first()
    if not promo:
        return f'Промокод с id {promo_id} не существует в БД.'
    promo.active = False
    promo.save()
    return f'Промокод с id {promo_id} теперь активен.'


@shared_task
def delete_limite_time_product(product_id):
    product = LimitTimeProduct.objects.filter(id=product_id).first()
    if not product:
        return f'Товар дня id:{product_id} не существует в БД.'

    product.delete()
    return f'Товар дня id:{product_id} удалён.'
