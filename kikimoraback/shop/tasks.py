from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from .models import *
import httpx
import re
import os
from dotenv import load_dotenv
load_dotenv()


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


@shared_task
def check_crm_changes():
    insales_url = os.getenv("INSALES_URL")
    sub_page = 1
    new_subcategories = []
    new_products = []
    new_photos = []

    with httpx.Client() as client:
        while True:
            sub_response = client.get(f"{insales_url}collections.json", params={'page': sub_page}).json()
            if not sub_response:
                break

            for subcat in sub_response:
                if "сайт" in subcat['title']:
                    if not Subcategory.objects.filter(subcategory_id=subcat['id']).exists():
                        new_subcategories.append(
                            Subcategory(
                                subcategory_id=subcat['id'],
                                name=subcat['title'].replace('сайт', ''),
                                category=Category.objects.get(category_id=1)
                            )
                        )

                    prod_response = client.get(f"{insales_url}collects.json", params={'collection_id': subcat['id']}).json()
                    if prod_response:
                        for product in prod_response:
                            prod_data = client.get(f"{insales_url}products/{product['product_id']}.json").json()
                            if not Product.objects.filter(product_id=prod_data['id']).exists():
                                new_product = Product(
                                    product_id=prod_data['id'],
                                    name=re.sub(r'\s*\(.*?\)\s*', '', prod_data['title']),
                                    description=prod_data['description'],
                                    price=float(prod_data['variants'][0]['price_in_site_currency']),
                                    weight=prod_data['variants'][0]['weight'],
                                    subcategory=Subcategory.objects.get(subcategory_id=subcat['id']),
                                    bonus=round(float(prod_data['variants'][0]['price_in_site_currency']) * 0.01)
                                )
                                new_products.append(new_product)

                                for image in prod_data['images']:
                                    new_photos.append(
                                        ProductPhoto(
                                            product=new_product,
                                            photo_url=image['external_id'],
                                            is_main=(image['position'] == 1)
                                        )
                                    )
            sub_page += 1

    with transaction.atomic():
        Subcategory.objects.bulk_create(new_subcategories, ignore_conflicts=True)
        Product.objects.bulk_create(new_products, ignore_conflicts=True)
        ProductPhoto.objects.bulk_create(new_photos, ignore_conflicts=True)