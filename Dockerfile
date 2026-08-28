FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy project
COPY postapp/ /app/

# Collect static files
ENV DJANGO_SETTINGS_MODULE=postapp.settings.prod
RUN python manage.py collectstatic --noinput

# Non-root user for security
RUN useradd -m -u 1000 postknob && chown -R postknob /app
USER postknob

EXPOSE 8000

CMD ["gunicorn", "postapp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
