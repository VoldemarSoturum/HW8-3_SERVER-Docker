# Лёгкий образ с Python
FROM python:3.11-slim

# Настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем только requirements для кеша
COPY EX2+ADDIONS-Stocks_products/requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходники проекта
COPY EX2+ADDIONS-Stocks_products/ .

# Значения по умолчанию для переменных окружения
ENV DJANGO_DEBUG=1 \
    DJANGO_ALLOWED_HOSTS="*"

# Порт, на котором слушает Django
EXPOSE 8000

# При запуске контейнера сначала мигрируем БД, потом стартуем сервер
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
