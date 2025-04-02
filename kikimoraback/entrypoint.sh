#!/bin/bash

# Выполняем миграции
python manage.py makemigrations
python manage.py migrate

# Запускаем задачу для инициализации кэша
python manage.py boot_cache

# Собираем статические файлы
python manage.py collectstatic --noinput

# Запускаем gunicorn
exec gunicorn --bind 0.0.0.0:8000 --capture-output kikimoraback.wsgi:application
