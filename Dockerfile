# Base image
FROM python:3.13.3-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user
RUN addgroup --system app && \
    adduser --system --ingroup app app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements/base.txt requirements/base.txt

RUN pip install --no-cache-dir -r requirements/base.txt

# Copy project files
COPY . .

# Collect static files at build time (needs dummy settings values so
# Django can boot without real secrets/DB access during build)
RUN SECRET_KEY=build-time-dummy-key \
    DEBUG=False \
    ALLOWED_HOSTS=* \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    python manage.py collectstatic --noinput

# Copy entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Change ownership to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]