# Database Migrations

Database migration files for schema changes.

## Usage

Run migrations using the migration script:
```bash
./infrastructure/scripts/migrate.sh
```

## Structure

Migrations should be named with timestamps:
- `001_initial_schema.sql`
- `002_add_users_table.sql`
- etc.

