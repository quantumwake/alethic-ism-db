#!/bin/sh
#set -e
echo "******* EXECUTION DATE: `date` ********"
#echo "Pass: $POSTGRES_PASSWORD"
echo "User: $POSTGRES_USER"
echo "Database: $POSTGRES_DB"
echo "Host: $POSTGRES_HOST"

# Wait for PostgreSQL to be ready
until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - executing bootstrap script"
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -f /scripts/bootstrap.sql

echo "Bootstrap completed successfully"
