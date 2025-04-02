from django.core.management.base import BaseCommand
from shop.tasks import boot_cache


class Command(BaseCommand):
    help = 'Запускает задачу для инициализации кэша'

    def handle(self, *args, **options):
        """
        Метод handle вызывается при выполнении команды.
        Здесь мы вызываем задачу Celery.
        """
        boot_cache.delay()
        self.stdout.write(self.style.SUCCESS('Задача для инициализации кэша отправлена'))