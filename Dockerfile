FROM python:3.12-slim

WORKDIR /app

# Копируем файлы
COPY requirements.txt .
COPY mirror_bot.py bot.py

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]
