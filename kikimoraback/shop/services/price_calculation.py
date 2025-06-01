import logging

from django.db.models import Prefetch
from django.utils import timezone

from ..models import ProductPhoto, ProductPhotoMini
from .caches import get_discount_cash, get_limit_product_cash

logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)


def calculate_prices(products):
    """
    Функция для расчета конечной стоимости товара с учетом всех скидок и акционных предложений.
    Первым в приоритете идет limittimeproduct, далее скидка дающая наибольшую экономию клиенту.
    Args:
        products (queryset): запрос из БД с информацией по всем товарам.
    Returns:
         dict: Словари с измененой ценой товаров и примененными к ним скидками.
    """
    now = timezone.now()

    # Собираем все связанные с товаром данные за 1 запрос
    products = products.prefetch_related(
        Prefetch("discount_set", queryset=get_discount_cash(), to_attr="active_discounts"),
        Prefetch(
            "subcategory__discount_set",  # Скидки подкатегорий
            queryset=get_discount_cash(),
            to_attr="active_subcategory_discounts",
        ),
        Prefetch(
            "limittimeproduct_set",
            queryset=get_limit_product_cash(),
            to_attr="active_limittimeproduct",
        ),
        Prefetch(
            "photos",
            queryset=ProductPhoto.objects.all(),  # Все фото для товаров
            to_attr="prefetched_photos",
        ),
        Prefetch(
            "mini_photos",
            queryset=ProductPhotoMini.objects.all(),
            to_attr="prefetched_mini_photos",
        ),
    )

    price_map = {}
    discounts_map = {}
    photos_map = {}
    photos_mini_map = {}
    for product in products:
        final_price = product.price
        applied_discounts = []

        if hasattr(product, "active_limittimeproduct") and product.active_limittimeproduct:
            offer = product.active_limittimeproduct[0]

            final_price = offer.price
            applied_discounts.append(
                {
                    "type": "limited",
                    "value": final_price,
                    "description": f"Акция: {offer.ammount} шт. до {offer.due.strftime('%d.%m %H:%M')}",
                }
            )

        else:
            discounts = []
            for discount in product.active_discounts:
                value = calculate_price_value(product, discount)
                if value <= 0:
                    value = product.price
                    logger.warning(
                        f"Цена товара стала меньше или равна нулю. "
                        f"ID товара: {product.product_id}, "
                        f"Текущая цена: {product.price}, "
                        f"ID скидки: {discount.discount_id}, "
                        f"Тип скидки: {discount.discount_type}, "
                        f"Значение скидки: {discount.value}"
                    )
                discounts.append((value, discount))

            for subcategory in product.subcategory.all():
                for discount in subcategory.active_subcategory_discounts:
                    value = calculate_price_value(product, discount)
                    if value <= 0:
                        value = product.price
                        logger.warning(
                            f"Цена товара стала меньше или равна нулю. "
                            f"ID товара: {product.product_id}, "
                            f"Текущая цена: {product.price}, "
                            f"ID скидки: {discount.discount_id}, "
                            f"Тип скидки: {discount.discount_type}, "
                            f"Значение скидки: {discount.value}"
                        )
                    discounts.append((value, discount))

            if discounts:
                best_discount = min(discounts, key=lambda x: x[0])
                final_price = best_discount[0]

                applied_discounts.append(
                    {
                        "type": best_discount[1].discount_type,
                        "value": best_discount[1].value,
                        "description": best_discount[1].description,
                    }
                )

        price_map[product.product_id] = final_price
        discounts_map[product.product_id] = applied_discounts
        photos_map[product.product_id] = [
            {
                "photo_id": photo.photo_id,
                "photo_url": photo.photo_url,
                "is_main": photo.is_main,
                "photo_description": photo.photo_description,
            }
            for photo in product.prefetched_photos
        ]
        photos_mini_map[product.product_id] = [
            {
                "photo_id": mini_photo.id,
                "photo_url": mini_photo.photo_url,
                "is_main": mini_photo.is_main,
                "photo_description": mini_photo.photo_description,
            }
            for mini_photo in product.prefetched_mini_photos
        ]

    return {
        "price_map": price_map,
        "discounts_map": discounts_map,
        "photos_map": photos_map,
        "mini_photo_map": photos_mini_map,
    }


def calculate_price_value(product, discount):
    """
    Вспомогательная функция для расчета скидки для товара.
    Args:
        product (Product): данные о товаре.
        discount (Discount): данные о скидке.

    Returns:
        int: Возвращает конечную стоимость товара после применения скидок.
    """
    if discount.discount_type == "percentage":
        return round(product.price * ((100 - discount.value) / 100))
    else:
        return product.price - discount.value
