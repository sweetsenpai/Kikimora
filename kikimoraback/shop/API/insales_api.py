import os

import requests
import json
from dotenv import load_dotenv
load_dotenv()

insales_url = os.getenv('INSALES_URL')

# response = requests.get(f'https://a85042b0d12227111cfd9073cf39320d:'
#                         f'4a7ec2e9ecb6748c41fe00dbd6f2c79d'
#                         f'@myshop-ciz622.myinsales.ru/admin/products.json', params={'title': 'Дикая слива'}).json()
# id = 1
# for i in range(3):
#     response = requests.get('https://a85042b0d12227111cfd9073cf39320d:'
#                         f'4a7ec2e9ecb6748c41fe00dbd6f2c79d'
#                         f'@myshop-ciz622.myinsales.ru/admin/products.json', params={'page': i+1, 'per_page': 100}).json()
#     for prod in response:
#         print(prod['id'])
#         print('Total products was found:', id)
#         id+=1
#
while True:
    response = requests.get('https://a85042b0d12227111cfd9073cf39320d:'
                            f'4a7ec2e9ecb6748c41fe00dbd6f2c79d'
                            f'@myshop-ciz622.myinsales.ru/admin/products.json')
    print(response.status_code)
# all_products = []
#
# for i in range(3):
#     response = requests.get('https://a85042b0d12227111cfd9073cf39320d:'
#                         f'4a7ec2e9ecb6748c41fe00dbd6f2c79d'
#                         f'@myshop-ciz622.myinsales.ru/admin/products.json', params={'page': i+1, 'per_page': 100})
#     if response.status_code == 200:
#         products = response.json()
#         all_products.extend(products)
#     else:
#         print(f"Error on page {i+1}: {response.status_code}")
#
# # Записываем все продукты в JSON файл
# with open("example.json", "w", encoding="utf-8") as file:
#     json.dump(all_products, file, ensure_ascii=False, indent=2)
#
# print('----------------------------------------------END---------------------------------------------------------')
# print(f"Saved {len(all_products)} products to example.json")
