#!/bin/sh
set -e

python <<'EOF'
import os
import socket
import sys
import time
import urllib.parse as urlparse

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL is not set — skipping wait-for-db")
    sys.exit(0)

parsed = urlparse.urlparse(database_url)
host = parsed.hostname
port = parsed.port or 5432

print(f"Waiting for database at {host}:{port}...")
while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            print("Database is accepting connections.")
            break
    except OSError:
        print("Database not ready, retrying in 1s...")
        time.sleep(1)
EOF

echo "Applying migrations..."
python manage.py migrate

echo "Syncing superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if email and password:
    user, created = User.objects.get_or_create(email=email, defaults={'is_staff': True, 'is_superuser': True})
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print('Created' if created else 'Updated', 'superuser:', email)
else:
    print('DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD not set, skipping superuser sync')
"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"