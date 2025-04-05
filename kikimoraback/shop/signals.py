import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import Discount, LimitTimeProduct, Product, ProductPhoto, Subcategory
from .services.caches import *
from .tasks import update_price_cache

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Subcategory)
def delete_related_products(sender, instance, **kwargs):
    """
    Удаляет все связанные товары и их фото при удалении подкатегории.
    """
    # Получаем все товары, привязанные к этой подкатегории
    related_products = instance.products.all()
    # Удаляем все связанные с товаром записи
    ProductPhoto.objects.filter(product__in=related_products).delete()
    Discount.objects.filter(product__in=related_products).delete()
    Discount.objects.filter(subcategory=instance).delete()
    LimitTimeProduct.objects.filter(product_id__in=related_products).delete()
    # Удаляем сами товары
    related_products.delete()


@receiver(pre_save, sender=Subcategory)
def update_related_products(sender, instance, **kwargs):
    """
    Обновляет товары, если изменилось поле 'visibility' у подкатегории.
    """
    if (
        instance.pk
    ):  # Проверяем, что объект уже существует (не создаётся, а обновляется)
        try:
            old_instance = Subcategory.objects.get(pk=instance.pk)
        except Subcategory.DoesNotExist:
            return

        # Проверяем, изменилось ли поле visibility
        if old_instance.visibility != instance.visibility:
            # Обновляем связанные товары
            Product.objects.filter(subcategory=instance).update(
                visibility=instance.visibility
            )


@receiver([post_save, post_delete])
def invalidate_cach(sender, instance, **kwargs):
    if sender in {Subcategory, Product, Discount, LimitTimeProduct}:

        if sender == Subcategory:
            subcategory_cache(True)
            active_products_cache(instance.pk, True)
            if Discount.objects.filter(subcategory=instance.pk):
                get_discount_cash(True)
            update_price_cache(forced=True)

        if sender == Product:
            active_products_cache(invalidate=True)
            get_discount_cash(True)
            get_discounted_product_data(True)
            get_limit_product_cash(True)
            update_price_cache(forced=True)

        if sender == LimitTimeProduct:
            get_limit_product_cash(True)
            active_products_cache(invalidate=True)
            update_price_cache(forced=True)
            get_discounted_product_data(True)

        if sender == Discount:
            get_discount_cash(True)
            active_products_cache(invalidate=True)
            update_price_cache(forced=True)
            get_discounted_product_data(True)
