from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import Subcategory, Product, ProductPhoto, Discount, LimitTimeProduct
import logging
logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Subcategory)
def delete_related_products(sender, instance, **kwargs):
    """
    Удаляет все связанные товары и их фото при удалении подкатегории.
    """
    # Получаем все товары, привязанные к этой подкатегории
    related_products = instance.products.all()
    # Удаляем фото товаров
    ProductPhoto.objects.filter(product__in=related_products).delete()
    Discount.objects.filter(product__in=related_products).delete()
    Discount.objects.filter(subcategory__in=instance).delete()
    LimitTimeProduct.objects.filter(product__in=related_products).delete()
    # Удаляем сами товары
    related_products.delete()


@receiver(pre_save, sender=Subcategory)
def update_related_products(sender, instance, **kwargs):
    """
    Обновляет товары, если изменилось поле 'visibility' у подкатегории.
    """
    if instance.pk:  # Проверяем, что объект уже существует (не создаётся, а обновляется)
        try:
            old_instance = Subcategory.objects.get(pk=instance.pk)
        except Subcategory.DoesNotExist:
            return

        # Проверяем, изменилось ли поле visibility
        if old_instance.visibility != instance.visibility:
            # Обновляем связанные товары
            Product.objects.filter(subcategory=instance).update(visibility=instance.visibility)