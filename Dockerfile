FROM python:3.11.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DJANGO_SETTINGS_MODULE=JobJab.settings
EXPOSE 8000
CMD ["bash", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 JobJab.asgi:application"]