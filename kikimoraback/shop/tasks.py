from celery import shared_task
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from .services.caches import *
from .models import *
from functools import wraps
from .services.price_calculation import calculate_prices
from .MongoIntegration.Order import Order
from .API.insales_api import send_new_order
import kikimoraback.settings as settings
import httpx
import re
import os
import logging
from dotenv import load_dotenv
import pymongo
from .services.email_verification import generate_email_token

load_dotenv()

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


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


@shared_task()
def new_order_email(order_data):
    # Формируем строку с перечислением товаров
    products_list = "".join(
        f"""
        <tr>
            <td style="border: 1px solid #ddd;">{product['name']}</td>
            <td style="border: 1px solid #ddd;">{product['quantity']}</td>
            <td style="border: 1px solid #ddd;">{product['price']} ₽</td>
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
        products_list += f"""
        <tr>
            <td style="border: 1px solid #ddd;">Доставка</td>
            <td style="border: 1px solid #ddd;">1</td>
            <td style="border: 1px solid #ddd;">{order_data['delivery_data']['cost']} ₽</td>
        </tr>
        """

    # HTML-содержимое письма
    html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h1 style="color: #4CAF50;">Спасибо за заказ!</h1>
                <p>Ваш заказ №<b>{order_data['insales']}</b> принят в работу.</p>
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
                    <p>Контакты: <a href="mailto:{os.getenv("KIKIMORA_EMAIL")}" style="color: #4CAF50; text-decoration: none;">{os.getenv("KIKIMORA_EMAIL")}</a> | Телефон: <a href="tel:{os.getenv("KIKIMORA_PHONE_RAW")}" style="color: #4CAF50; text-decoration: none;">{os.getenv("KIKIMORA_PHONE")}</a></p>
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
        subject=f"Кикимора заказ №{order_data['insales']}",
        body=html_content,
        from_email=os.getenv("EMAIL"),
        to=[order_data['customer_data']['email']],
    )

    # Указываем, что содержимое письма в формате HTML
    email_message.content_subtype = "html"

    # Отправляем письмо
    email_message.send(fail_silently=False)

    return


@shared_task
def send_confirmation_email(user):
    token = generate_email_token(user.user_id)
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


@shared_task(bind=True, max_retries=3)
def check_crm_changes(self):
    logger.info("Task `check_crm_changes` started.")
    insales_url = os.getenv("INSALES_URL")
    new_subcategories = []
    new_products = []
    new_photos = []

    try:
        with httpx.Client() as client:
                # Получаем данные о подкатегориях (коллекциях)
            sub_response = client.get(f"{insales_url}collections.json", params={'parent_id': 30736737}).json()
            if not sub_response:
                logger.error("Не удалось получить ответ от insales при обновлении БД.")
            sub_list = [subcategory['id'] for subcategory in sub_response]
            Subcategory.objects.exclude(subcategory_id__in=sub_list).delete()
            for subcat in sub_response:
                # Проверяем, существует ли подкатегория в базе данных
                try:
                    text = subcat.get('description', '')
                    if isinstance(text, str):
                        text = re.sub(r'<.*?>', '', text)
                    else:
                        text=''
                    subcategory, created = Subcategory.objects.update_or_create(
                        subcategory_id=subcat['id'],
                        defaults={
                            'name': subcat['title'],
                            'category': Category.objects.get(category_id=1),
                            'text': text,
                            'permalink': subcat['permalink']
                        }
                    )
                except Exception as e:
                    logger.error(f"Во время создания новой категории произошла ошибка."
                                 f"\nERROR: {e}"
                                 f"\nSUBCATEGORY DATA:{subcat}")
                if created:
                    new_subcategories.append(subcategory)

                # Получаем товары из коллекции
                prod_response = client.get(f"{insales_url}collects.json", params={'collection_id': subcat['id']}).json()
                if prod_response:
                    for product in prod_response:
                        # Получаем данные о товаре
                        prod_data = client.get(f"{insales_url}products/{product['product_id']}.json").json()
                        bonus = float(prod_data['variants'][0]['price_in_site_currency']) * 0.1 if \
                        float(prod_data['variants'][0]['price_in_site_currency']) < 4000 else float(
                            prod_data['variants'][0]['price_in_site_currency']) * 0.05
                        weight = prod_data['variants'][0].get('weight')
                        if not prod_data['variants'][0]['quantity'] or prod_data['variants'][0]['quantity'] == 0:
                            avileble = False
                        else:
                            avileble = True
                        if not weight:
                            weight = 0
                        try:
                            product_obj, created = Product.objects.update_or_create(
                                product_id=prod_data['id'],
                                defaults={
                                    'name': re.sub(r'\s*\(.*?\)\s*', '', prod_data['title']),
                                    'description': prod_data['description'],
                                    'price': float(prod_data['variants'][0]['price_in_site_currency']),
                                    'weight': weight,
                                    'bonus': round(bonus),
                                    'permalink': prod_data['permalink'],
                                    'available': avileble
                                }
                            )
                            if created:
                                # Привязываем подкатегорию к товару
                                product_obj.subcategory.add(subcategory)
                                new_products.append(product_obj)
                                # Добавляем фотографии товара
                                for image in prod_data['images']:
                                    if image['external_id']:
                                        new_photos.append(
                                            ProductPhoto(
                                                product=product_obj,
                                                photo_url=image['url'],
                                                is_main=(image['position'] == 1)
                                            )
                                        )
                                    elif image['original_url']:
                                        new_photos.append(
                                            ProductPhoto(
                                                product=product_obj,
                                                photo_url=image['original_url'],
                                                is_main=(image['position'] == 1)
                                            )
                                        )
                            else:
                                product_obj.subcategory.add(subcategory)
                                for image in prod_data['images']:
                                    if image['external_id']:
                                        obj, created = ProductPhoto.objects.get_or_create(
                                            photo_url=image['external_id'],
                                            defaults={
                                                'product': product_obj,
                                                'is_main': (image['position'] == 1)
                                            }
                                        )
                                    elif image['original_url']:
                                        obj, created = ProductPhoto.objects.get_or_create(
                                            photo_url=image['original_url'],
                                            defaults={
                                                'product': product_obj,
                                                'is_main': (image['position'] == 1)
                                            }
                                        )

                        except Exception as e:
                            logger.error(f"Во время записи нового товара в БД произошла ошибка."
                                         f"\n PRODUCT DATA: {prod_data}"
                                         f"\n ERROR: {e}")
                            pass

        # Используем транзакцию и bulk_create для массовой вставки товаров, подкатегорий и фотографий
        with transaction.atomic():
            Subcategory.objects.bulk_create(new_subcategories, ignore_conflicts=True)
            Product.objects.bulk_create(new_products, ignore_conflicts=True)
            ProductPhoto.objects.bulk_create(new_photos, ignore_conflicts=True)

        logger.info(
            f"Successfully added {len(new_subcategories)} subcategories, {len(new_products)} products, and {len(new_photos)} photos.")

        update_price_cache(forced=True)
    except Exception as e:
        logger.error(f"Error in `check_crm_changes`: {e}")
        self.retry(countdown=2 ** self.request.retries)


@shared_task
def clean_up_mongo():
    collection = pymongo.MongoClient(os.getenv("MONGOCON"))['kikimora']['cart']
    result = collection.delete_many({"unregistered": True})
    logger.info(f"Удалено {result.deleted_count} корзин с меткой unregistered.")


def cache_result(cache_key: str, timeout: int = None):
    """
    Декоратор для кэширования.

    :param cache_key: Ключ для хранения результата в кэше.
    :param timeout: Время жизни кэша в секундах. Если None, кэш будет вечным.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Извлекаем параметр forced из kwargs, если он есть
            forced = kwargs.pop('forced', False)

            # Проверяем, есть ли результаты в кэше
            cached_result = cache.get(cache_key)
            if cached_result is not None and not forced:
                return cached_result
            # Кэшируем полученные данные и сохраняем
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator


@shared_task
@cache_result("all_products_prices", timeout=None)
def update_price_cache(forced=False):
    """
    Фоновая задача для предрасчета цен товаров.
    :param forced: Используется для принудительного создания нового кэша, даже если он есть. По умолчанию false.
    """
    products = active_products_cash()
    result = calculate_prices(products)

    # Создаем список товаров с скидками
    products_with_discounts = [
        product_id for product_id, discounts in result['discounts_map'].items() if discounts
    ]

    # Сохраняем список товаров с скидками в отдельном кэше
    cache.set("products_with_discounts", products_with_discounts, timeout=None)

    logger.info("Кэширование цен товаров прошло успешно.")
    return result
# TODO релизовать задачу для обновления всех свзяанных кэшей
# @shared_task
# def update_related_caches():
#     """
#     Обновляет все связанные кэши.
#     """
#     cache.delete("all_products_prices")
#     cache.delete("products_with_discounts")
#
#     from .tasks import update_price_cache
#     update_price_cache.delay(forced=True)
#
#     logger.info("Все связанные кэши успешно обновлены.")


@shared_task(bind=True, max_retries=3)
def process_payment_succeeded(self, payment_id):
    try:
        user_order = Order()
        if not user_order.ping():
            logger.error(f"Ошибка подключения к базе данных при обработке платежа {payment_id}.")
            return

        user_order_data = user_order.get_order_by_payment(payment_id)

        # Начисление бонусов
        if user_order_data['add_bonuses']:
            UserBonusSystem.add_bonus(user_order_data['customer'], user_order_data['add_bonuses'])

        # Отправка заказа в InSales
        insales_order_new = send_new_order(user_order_data)
        if insales_order_new:
            user_order.insert_insales_number(payment_id=payment_id, insales_order_number=insales_order_new)
            user_order_data['insales'] = insales_order_new

            del user_order_data['_id']
            # Просто удалил поле _id воизбежания ошибки при сериализации=)

            new_order_email.delay(user_order_data)
        else:
            logger.error(f"Не удалось загрузить заказ {payment_id} в CRM.")
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа {payment_id}: {e}")
        self.retry(countdown=2 ** self.request.retries)  # Повторная попытка через экспоненциальное время ожидания


@shared_task(bind=True, max_retries=3)
def process_payment_canceled(self, payment_id):
    try:
        user_order = Order()
        user_order_data = user_order.get_order_by_payment(payment_id)

        # Возврат бонусов
        if user_order_data['bonuses_deducted']:
            UserBonusSystem.add_bonus(user_order_data['customer'], user_order_data['bonuses_deducted'])
    except Exception as e:
        logger.error(f"Ошибка при обработке отмененного платежа {payment_id}: {e}")
        self.retry(countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def add_discount_to_insales_order(self, order_id, discount):
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
