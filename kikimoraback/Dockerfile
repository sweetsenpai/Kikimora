# Используем легковесный Python
FROM python:3.10.4-slim-bullseye

# Устанавливаем переменные окружения
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=kikimoraback.settings

# Создаём рабочую директорию
WORKDIR /kikimoraback

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Копируем скрипт entrypoint.sh
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

# Открываем порт (если нужно)
EXPOSE 8000

# Устанавливаем entrypoint.sh как точку входа
ENTRYPOINT ["entrypoint.sh"]