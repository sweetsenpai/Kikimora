from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Subcategory, Product, ProductPhoto
import logging
logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Subcategory)
def delete_related_products(sender, instance, **kwargs):
    """
    Удаляет все связанные товары и их фото при удалении подкатегории.
    """
    # Получаем все товары, привязанные к этой подкатегории
    related_products = Product.objects.filter(subcategory=instance)

    # Удаляем фото товаров
    ProductPhoto.objects.filter(product__in=related_products).delete()

    # Удаляем сами товары
    related_products.delete()
