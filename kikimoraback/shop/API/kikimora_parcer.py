import requests
import time
import json
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scroll_to_bottom():
    # Прокрутка страницы на фиксированное расстояние
    browser.execute_script("window.scrollBy(0, 1000);")
    time.sleep(2)  # Подождать немного, чтобы элементы подгрузились


def get_products_names(url='', product_names=None):
    if product_names is None:
        product_names = []
    try:
        browser.get(url)

        # Ожидаем загрузки первых элементов с названиями товаров
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'js-store-prod-name')]"))
        )

        product_names = product_names
        last_count = 0

        while True:
            scroll_to_bottom()

            # Находим все элементы с названиями товаров
            current_names = browser.find_elements(By.XPATH, "//div[contains(@class, 'js-store-prod-name')]")

            # Добавляем новые уникальные элементы в список
            new_names = [name.text.strip() for name in current_names if name.text.strip()]
            new_count = len(new_names)

            # Если новые элементы появились, добавляем их в список
            if new_count > last_count:
                product_names.extend(new_names[last_count:])  # Добавляем только новые товары
                last_count = new_count
            else:
                # Если новых элементов не появилось, то достигли конца
                break
        print("Названия товаров:")
        for name in product_names:
            print(name)
        next_page = browser.find_element(By.XPATH, "//div[contains(@class, 't-store__pagination__item_next')]")
        if next_page:
            next_page.click()
            get_products_names(browser.current_url, product_names=product_names)

    finally:
        # Закрываем браузер
        return product_names


base_url = 'https://kikimorashop.ru'

response = requests.get(base_url).text
options = Options()
browser = webdriver.Firefox(options=options)
soup = BS(response, "html.parser")
product_cat_dict = {}
for a in soup.findAll(class_='t966__menu-link'):
    if a.text=='   Все товары    ':
        continue
    sub_url = a['href']
    name_cat = ' '.join(a.text.split())
    product_cat_dict[name_cat]=get_products_names(base_url+sub_url)
    print(product_cat_dict)

browser.quit()
with open('../views/output.json', 'w', encoding='utf-8') as json_file:
    json.dump(product_cat_dict, json_file, ensure_ascii=False, indent=4)

