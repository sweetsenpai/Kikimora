#!/bin/bash

# Выполняем миграции
python manage.py makemigrations
python manage.py migrate

# Собираем статик в /var/www/kikimora/static/
python manage.py collectstatic --noinput

# Запускаем gunicorn
exec gunicorn --bind 0.0.0.0:8000 --capture-output kikimoraback.wsgi:application

