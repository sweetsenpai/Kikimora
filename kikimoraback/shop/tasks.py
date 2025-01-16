from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
from .models import *
import httpx
import re
import os
import logging
import pymongo
from .MongoIntegration.Cart import Cart
from dotenv import load_dotenv
import pymongo
import datetime

load_dotenv()

logger = logging.getLogger(__name__)


@shared_task
def new_admin_mail(password, email):
    # Создаем HTML-контент письма
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
        from_email='settings.EMAIL_HOST_USER',
        to=[email],
    )

    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)
    return


@shared_task()
def new_order_email(order_data):
    # Формируем строку с перечислением товаров
    products_list = "".join(
        f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{product['name']}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{product['quantity']}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{product['price']} ₽</td>
        </tr>
        """
        for product in order_data["products"]
    )

    total = order_data["total"]
    delivery_date = order_data['delivery_data']['date'].strftime("%d.%m.%Y")

    if order_data['delivery_data']['method'] == "Самовывоз":
        delivery_info = f"""
            <p>Ваш заказ можно будет забрать по адресу: <b>Санкт-Петербург, ул. 11-я Красноармейская, 11, строение 3.</b></p>
            <p>Выбранная дата и время получения: <b>{delivery_date} {order_data['delivery_data']['time']}</b></p>
        """
    else:
        delivery_info = f"""
            <p>Доставка по адресу: <b>{order_data['delivery_data']['street']} {order_data['delivery_data']['building']}, {order_data['delivery_data']['apartment']}</b></p>
            <p>Выбранная дата и время доставки: <b>{delivery_date} {order_data['delivery_data']['time']}</b></p>
        """

    # HTML-содержимое письма
    html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h1 style="color: #4CAF50;">Спасибо за заказ!</h1>
                <p>Ваш заказ №<b>1488</b> принят в работу.</p>
                <p>Детали заказа:</p>
                <table style="border-collapse: collapse; width: 100%; text-align: left;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="border: 1px solid #ddd; padding: 8px;">Товар</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Количество</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">Цена</th>
                        </tr>
                    </thead>
                    <tbody>
                        {products_list}
                    </tbody>
                </table>
                <p><strong>Общая стоимость: {total} ₽</strong></p>
                {delivery_info}
                <p>Спасибо за ваш заказ! Ждем вас снова.</p>

                <!-- Подвал -->
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                <footer style="text-align: center; color: #888; font-size: 14px;">
                    <p>С уважением, команда мастерской "Кикимора"</p>
                    <p>Контакты: <a href="mailto:info@kikimora.ru" style="color: #4CAF50; text-decoration: none;">info@kikimora.ru</a> | Телефон: <a href="tel:+79992099638" style="color: #4CAF50; text-decoration: none;">+7(999) 209-96-38</a></p>
                    <p>Адрес: Санкт-Петербург, ул. 11-я Красноармейская, 11, строение 3</p>
                    <p>Следите за нами: 
                        <a href="https://vk.com/kikimora" style="color: #4CAF50; text-decoration: none;">ВКонтакте</a> | 
                        <a href="https://instagram.com/kikimora" style="color: #4CAF50; text-decoration: none;">Instagram</a>
                    </p>
                </footer>
            </body>
        </html>
    """

    # Создаем сообщение
    email_message = EmailMessage(
        subject=f"Кикимора заказ №1488",
        body=html_content,
        from_email='settings.EMAIL_HOST_USER',
        to=[order_data['customer_data']['email']],
    )

    # Указываем, что содержимое письма в формате HTML
    email_message.content_subtype = "html"

    # Отправляем письмо
    email_message.send(fail_silently=False)

    return


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
    product = LimitTimeProduct.objects.filter(product_id=product_id).first()
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
                                    for prod_id in prod_for_delete:
                                        Product.objects.get(product_id=prod_id).subcategory.remove(subcategory)

                            for product in prod_response:
                                if product['product_id'] in product_for_create:
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


@shared_task
def clean_up_mongo():
    collection = pymongo.MongoClient(os.getenv("MONGOCON"))['kikimora']['cart']
    result = collection.delete_many({"unregistered": True})
    logger.info(f"Удалено {result.deleted_count} корзин с меткой unregistered.")
