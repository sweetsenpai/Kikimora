import requests
import uuid
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('YANDEX_TOKEN')
headers={"Authorization": f"Bearer {token}",
         'Accept-Language': 'ru/ru'}
data= {
        "route_points": [
            {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
            {"fullname": "Санкт-Петербург, Московский проспект 135"}],
    }


yandex_response = requests.post('https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price', headers=headers, json=data)

if yandex_response.status_code == 200:
    print('Стоимость доставки: ', yandex_response.json()['price'])
    print('Расстояние доставки: ', yandex_response.json()['distance_meters'])
elif yandex_response.status_code == 400:
    print('Неудается найти указанный адрес, проверьте правильность введенного адреса.')
else:
    print(yandex_response.json())
    print('В данный момент не возможно осуществить доставку.')

