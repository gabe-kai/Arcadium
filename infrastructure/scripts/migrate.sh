#!/bin/bash

# Database migration script

set -e

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-arcadium}"
DB_NAME="${DB_NAME:-arcadium}"
DB_PASSWORD="${DB_PASSWORD:-arcadium_dev}"

MIGRATIONS_DIR="./infrastructure/database/migrations"

echo "Running database migrations..."

# Export password for psql
export PGPASSWORD=$DB_PASSWORD

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Run each migration file
for migration in $(ls -1 $MIGRATIONS_DIR/*.sql 2>/dev/null | sort); do
    echo "Running migration: $(basename $migration)"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $migration
done

echo "Migrations complete!"

