from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Установите переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kikimoraback.settings')

app = Celery('kikimoraback')

# Загрузите конфигурацию Celery из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживайте задачи в приложениях Django
app.autodiscover_tasks()
