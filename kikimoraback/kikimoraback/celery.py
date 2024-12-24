from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Установите переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kikimoraback.settings')

app = Celery('kikimoraback')

# Загрузите конфигурацию Celery из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживайте задачи в приложениях Django
app.autodiscover_tasks()

# Добавьте расписание для задачи
app.conf.beat_schedule = {
    'check-crm-changes-every-hour': {
        'task': 'shop.tasks.check_crm_changes',  # Полное имя вашей задачи
        'schedule': crontab(minute='0', hour='*/1'),  # Каждый час в начале часа
    },
}
