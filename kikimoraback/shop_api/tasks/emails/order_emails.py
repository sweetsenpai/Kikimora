import logging

from celery import shared_task
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


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
    delivery_date = order_data["delivery_data"]["date"].strftime("%d.%m.%Y")

    if order_data["delivery_data"]["method"] == "Самовывоз":
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
        to=[order_data["customer_data"]["email"]],
    )

    # Указываем, что содержимое письма в формате HTML
    email_message.content_subtype = "html"

    # Отправляем письмо
    email_message.send(fail_silently=False)

    return
