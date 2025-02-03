FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные библиотеки для сборки psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Копируем requirements и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт 8000
EXPOSE 8000

CMD ["python", "main.py"]
