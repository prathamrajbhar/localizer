#!/bin/bash
# Database Initialization Script

set -e

echo "Initializing database..."

# Wait for PostgreSQL to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run Alembic migrations
cd /app
alembic upgrade head

echo "Database initialization complete!"

