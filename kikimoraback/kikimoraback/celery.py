from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kikimoraback.settings')

app = Celery('kikimoraback')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['shop_api.tasks'])

app.conf.beat_schedule = {
    'check-crm-changes-every-15-minute': {
        'task': 'shop_api.tasks.db_tasks.sql.filling_db_tasks.check_crm_changes',
        'schedule': crontab(minute='*/15'),
    },
    'cleanup-mongo-four-hour': {
        'task': 'shop_api.tasks.db_tasks.mongo.mongo_tasks.clean_up_mongo',
        'schedule': crontab(minute='0', hour='4'),
    }
}
