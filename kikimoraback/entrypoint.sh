#!/bin/bash

# Выполняем миграции
python manage.py makemigrations
python manage.py migrate

# Запускаем задачу для инициализации кэша
python manage.py boot_cache

# Собираем статические файлы
python manage.py collectstatic --noinput

# Запускаем gunicorn
exec uvicorn kikimoraback.asgi:application --host 0.0.0.0 --port 8000 --lifespan off
