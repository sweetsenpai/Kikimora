import logging
import os
import re

from django.db import transaction
from django.template.loader import render_to_string

import httpx
from celery import shared_task

from ..cache_tasks.cache_prices_tasks import update_price_cache

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


@shared_task(bind=True, max_retries=3)
def check_crm_changes(self):
    logger.info("Task `check_crm_changes` started.")
    insales_url = os.getenv("INSALES_URL")
    new_subcategories = []
    new_products = []
    new_photos = []
    new_mini_photos = []

    try:
        with httpx.Client() as client:
            # Получаем данные о подкатегориях (коллекциях)
            sub_response = client.get(
                f"{insales_url}collections.json", params={"parent_id": 30736737}
            ).json()
            if not sub_response:
                logger.error("Не удалось получить ответ от insales при обновлении БД.")
            sub_list = [subcategory["id"] for subcategory in sub_response]
            Subcategory.objects.exclude(subcategory_id__in=sub_list).delete()
            for subcat in sub_response:
                # Проверяем, существует ли подкатегория в базе данных
                try:
                    text = subcat.get("description", "")
                    if isinstance(text, str):
                        text = re.sub(r"<.*?>", "", text)
                    else:
                        text = ""
                    subcategory, created = Subcategory.objects.update_or_create(
                        subcategory_id=subcat["id"],
                        defaults={
                            "name": subcat["title"],
                            "category": Category.objects.get(category_id=1),
                            "text": text,
                            "permalink": subcat["permalink"],
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Во время создания новой категории произошла ошибка."
                        f"\nERROR: {e}"
                        f"\nSUBCATEGORY DATA:{subcat}"
                    )
                if created:
                    new_subcategories.append(subcategory)

                # Получаем товары из коллекции
                prod_response = client.get(
                    f"{insales_url}collects.json",
                    params={"collection_id": subcat["id"]},
                ).json()
                if prod_response:
                    for product in prod_response:
                        # Получаем данные о товаре
                        prod_data = client.get(
                            f"{insales_url}products/{product['product_id']}.json",
                            timeout=10,
                        ).json()
                        bonus = (
                            float(prod_data["variants"][0]["price_in_site_currency"]) * 0.1
                            if float(prod_data["variants"][0]["price_in_site_currency"]) < 4000
                            else float(prod_data["variants"][0]["price_in_site_currency"]) * 0.05
                        )
                        weight = prod_data["variants"][0].get("weight")
                        if prod_data["variants"][0]["quantity"] == 0:
                            available = False
                        else:
                            available = True
                        if not weight:
                            weight = 0
                        try:
                            product_obj, created = Product.objects.update_or_create(
                                product_id=prod_data["id"],
                                defaults={
                                    "name": re.sub(r"\s*\(.*?\)\s*", "", prod_data["title"]),
                                    "description": prod_data["description"],
                                    "price": float(
                                        prod_data["variants"][0]["price_in_site_currency"]
                                    ),
                                    "weight": weight,
                                    "bonus": round(bonus),
                                    "permalink": prod_data["permalink"],
                                    "available": available,
                                },
                            )
                            if created:
                                # Привязываем подкатегорию к товару
                                product_obj.subcategory.add(subcategory)
                                new_products.append(product_obj)
                                # Добавляем фотографии товара
                                for image in prod_data["images"]:
                                    if image["external_id"]:
                                        new_photos.append(
                                            ProductPhoto(
                                                product=product_obj,
                                                photo_url=image["url"],
                                                is_main=(image["position"] == 1),
                                            )
                                        )
                                    elif image["original_url"]:
                                        new_photos.append(
                                            ProductPhoto(
                                                product=product_obj,
                                                photo_url=image["original_url"],
                                                is_main=(image["position"] == 1),
                                            )
                                        )
                                    if image["large_url"]:
                                        new_mini_photos.append(
                                            ProductPhotoMini(
                                                product=product_obj,
                                                photo_url=image["large_url"],
                                                is_main=(image["position"] == 1),
                                            )
                                        )

                            else:
                                product_obj.subcategory.add(subcategory)
                                for image in prod_data["images"]:
                                    if image["external_id"]:
                                        obj, created = ProductPhoto.objects.get_or_create(
                                            photo_url=image["external_id"],
                                            defaults={
                                                "product": product_obj,
                                                "is_main": (image["position"] == 1),
                                            },
                                        )
                                    elif image["original_url"]:
                                        obj, created = ProductPhoto.objects.get_or_create(
                                            photo_url=image["original_url"],
                                            defaults={
                                                "product": product_obj,
                                                "is_main": (image["position"] == 1),
                                            },
                                        )
                                    if image["large_url"]:
                                        obj, created = ProductPhotoMini.objects.get_or_create(
                                            photo_url=image["large_url"],
                                            defaults={
                                                "product": product_obj,
                                                "is_main": (image["position"] == 1),
                                            },
                                        )

                        except Exception as e:
                            logger.error(
                                f"Во время записи нового товара в БД произошла ошибка."
                                f"\n PRODUCT DATA: {prod_data}"
                                f"\n ERROR: {e}"
                            )
                            pass

        # Используем транзакцию и bulk_create для массовой вставки товаров, подкатегорий и фотографий
        with transaction.atomic():
            Subcategory.objects.bulk_create(new_subcategories, ignore_conflicts=True)
            Product.objects.bulk_create(new_products, ignore_conflicts=True)
            ProductPhoto.objects.bulk_create(new_photos, ignore_conflicts=True)
            ProductPhotoMini.objects.bulk_create(new_mini_photos, ignore_conflicts=True)

        logger.info(
            f"Successfully added {len(new_subcategories)} subcategories, {len(new_products)} products, and {len(new_photos)} photos."
        )
        update_price_cache(forced=True)
    except Exception as e:
        update_price_cache(forced=True)
        logger.error(f"Error in `check_crm_changes`: {e}")
        self.retry(countdown=2**self.request.retries)
