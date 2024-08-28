import requests
import uuid
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('YANDEX_TOKEN')


class YandexDelivery:
    host_url = 'https://b2b.taxi.yandex.net'
    my_addres = ''

    def __init__(self, token, client_addres):
        self.token = token
        self.client_addres = client_addres

    def calculate_delivery(self):
        req_result = requests.api.post(url=self.host_url, headers={"Authorization": "Bearer bafe64a70e3c4c269f70ebdfbe3f5f86"})
        return req_result


a = YandexDelivery(TOKEN, 'test')
print(a.calculate_delivery().text)
