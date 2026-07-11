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

echo "Starting application..."
exec "$@"