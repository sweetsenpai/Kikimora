# shop/services/delivery/yandex_delivery_service.py

import os
import requests
import logging

from dotenv import load_dotenv
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("shop")
load_dotenv()

class DeliveryService:
    MAX_RANGE = 5000
    ADD_COST = 100

    def __init__(self):
        self.token = os.getenv("YANDEX_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": "ru/ru"
        }

    def calculate(self, user_id: str, delivery_data: dict) -> Response:
        response = Response()

        if not delivery_data or not delivery_data.get("address"):
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"error": "Не передан адрес для расчета доставки."}
            return response

        address = delivery_data["address"]

        payload = {
            "route_points": [
                {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
                {"fullname": f"Санкт-Петербург, {address}"},
            ]
        }

        try:
            yandex_response = requests.post(
                "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price",
                headers=self.headers,
                json=payload,
            )
        except requests.RequestException as e:
            logger.critical(f"Ошибка при запросе к API Яндекс: {e}")
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            response.data = {
                "error": "Ошибка при расчете стоимости доставки. Повторите позже или обратитесь в магазин."
            }
            return response

        try:
            yandex_data = yandex_response.json()
        except ValueError:
            logger.error(f"Некорректный JSON от API Яндекс. Статус: {yandex_response.status_code}")
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            response.data = {
                "error": "Сервис доставки временно недоступен. Перезагрузите страницу и попробуйте ещё раз."
            }
            return response

        if yandex_response.ok:
            distance_meters = yandex_data["distance_meters"]
            price = round(float(yandex_data["price"]))

            if distance_meters <= self.MAX_RANGE:
                price += self.ADD_COST
            elif distance_meters <= self.MAX_RANGE * 2:
                price += self.ADD_COST * 2
            else:
                price += self.ADD_COST * 3

            response.status_code = status.HTTP_200_OK
            response.data = {"price": price, "distance_meters": distance_meters}
            return response

        return self._handle_error(yandex_response.status_code, yandex_data, address, response)

    def _handle_error(self, code: int, data: dict, address: str, response: Response) -> Response:
        default_error = "Сейчас сервис доставки недоступен. Вы можете оформить доставку самостоятельно или обратиться в магазин."

        if code == 400:
            logger.error(f"Ошибка расчета стоимости. Address: {address} Error: {data}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data = {"error": "Не удалось рассчитать стоимость доставки. Проверьте правильность введенного адреса."}
        elif code == 401:
            logger.critical("Неверный токен yandex-delivery.")
            response.status_code = status.HTTP_401_UNAUTHORIZED
            response.data = {"error": default_error}
        else:
            logger.error(f"Непредвиденная ошибка при расчете. Address: {address} Error: {data}")
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            response.data = {"error": default_error}
        return response
