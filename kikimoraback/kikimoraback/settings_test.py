"""
Настройки Django для запуска тестов.
Этот файл наследует базовые настройки и переопределяет нужные параметры для тестирования.
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'kikimoraback'))

from .settings_dev import *  # Наследуем настройки разработки
import tempfile
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_celery_beat",
    'shop',
    'shop_api',
]


# Отключаем Celery для тестов, заменяя его на синхронный режим
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'

# Используем быструю тестовую БД в памяти
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Используем in-memory SQLite для скорости
    }
}

# Отключаем кэширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Отключаем проверку паролей для ускорения тестов
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Отключаем CSRF проверку для тестовых запросов
MIDDLEWARE = [m for m in MIDDLEWARE if 'csrf' not in m.lower()]

# Отключаем логирование или перенаправляем в файл
LOGGING = {
}

MEDIA_ROOT = tempfile.mkdtemp()

# Отключаем отправку реальных писем
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Ускоряем тесты, отключая миграции
MIGRATION_MODULES = {
    'auth': None,
    'contenttypes': None,
    'sessions': None,
    'admin': None,
    'shop': None,
    'shop_api': None,
    # Добавьте другие ваши приложения, чтобы отключить их миграции во время теста
}

# Добавьте сюда мок-настройки для внешних сервисов, которые вы используете
# Например:
# PAYMENT_GATEWAY_URL = 'http://mock-payment-gateway'

# Используем быстрые тестовые шаблонные движки
# Update templates configuration for tests
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
