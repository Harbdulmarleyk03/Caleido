#!/bin/sh

until pg_isready -h db -p 5432 -U $POSTGRES_USER
do
    echo "Waiting for PostgreSQL..."
    sleep 1
done

echo "Applying migrations..."
python manage.py migrate

echo "Starting application..."
exec "$@"