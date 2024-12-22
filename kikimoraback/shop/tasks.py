from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from .models import *
import httpx
import re
import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


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
    logger.info("Task `check_crm_changes` started.")
    insales_url = os.getenv("INSALES_URL")
    sub_page = 1
    new_subcategories = []
    new_products = []
    new_photos = []

    try:
        with httpx.Client() as client:
            while True:
                # Получаем данные о подкатегориях (коллекциях)
                sub_response = client.get(f"{insales_url}collections.json", params={'page': sub_page}).json()
                if not sub_response:
                    break

                for subcat in sub_response:
                    if "сайт" in subcat['title']:
                        # Проверяем, существует ли подкатегория в базе данных
                        subcategory, created = Subcategory.objects.get_or_create(
                            subcategory_id=subcat['id'],
                            defaults={
                                'name': subcat['title'].replace('сайт', '').strip(),
                                'category': Category.objects.get(category_id=1)
                            }
                        )
                        if created:
                            new_subcategories.append(subcategory)

                        # Получаем товары из коллекции
                        prod_response = client.get(f"{insales_url}collects.json", params={'collection_id': subcat['id']}).json()
                        if prod_response:
                            if not created:
                                product_in_db = set(subcategory.products.values_list('product_id', flat=True))
                                product_in_crm = {item['product_id'] for item in prod_response}
                                prod_for_delete = product_in_db - product_in_crm
                                product_for_create = product_in_crm - prod_for_delete
                                if prod_for_delete:
                                    logger.info(f"Список ID для удаления связей:{prod_for_delete}")
                                    for prod_id in prod_for_delete:
                                        Product.objects.get(product_id=prod_id).subcategory.remove(subcategory)
                                    logger.info(f"Связи успешно удаленны из БД")

                            for product in prod_response:
                                if product in product_for_create:
                                    # Получаем данные о товаре
                                    prod_data = client.get(f"{insales_url}products/{product['product_id']}.json").json()

                                    # Проверяем, существует ли товар в базе
                                    product_obj, created = Product.objects.get_or_create(
                                        product_id=prod_data['id'],
                                        defaults={
                                            'name': re.sub(r'\s*\(.*?\)\s*', '', prod_data['title']),
                                            'description': prod_data['description'],
                                            'price': float(prod_data['variants'][0]['price_in_site_currency']),
                                            'weight': prod_data['variants'][0]['weight'],
                                            'bonus': round(float(prod_data['variants'][0]['price_in_site_currency']) * 0.01),
                                        }
                                    )

                                    if created:
                                        # Привязываем подкатегорию к товару
                                        product_obj.subcategory.add(subcategory)
                                        new_products.append(product_obj)

                                        # Добавляем фотографии товара
                                        for image in prod_data['images']:
                                            new_photos.append(
                                                ProductPhoto(
                                                    product=product_obj,
                                                    photo_url=image['external_id'],
                                                    is_main=(image['position'] == 1)
                                                )
                                            )
                                    else:
                                        product_obj.subcategory.add(subcategory)
                                        logger.info(f"Связи товара успешно добавлена в БД")

                sub_page += 1

        # Используем транзакцию и bulk_create для массовой вставки товаров, подкатегорий и фотографий
        with transaction.atomic():
            Subcategory.objects.bulk_create(new_subcategories, ignore_conflicts=True)
            Product.objects.bulk_create(new_products, ignore_conflicts=True)
            ProductPhoto.objects.bulk_create(new_photos, ignore_conflicts=True)

        logger.info(
            f"Successfully added {len(new_subcategories)} subcategories, {len(new_products)} products, and {len(new_photos)} photos.")

    except Exception as e:
        logger.error(f"Error in `check_crm_changes`: {e}")
        raise
