#!/bin/bash

# Выполняем миграции
python manage.py makemigrations
python manage.py migrate

# Запускаем сервер через gunicorn
exec gunicorn --bind 0.0.0.0:8000 kikimoraback.wsgi:application