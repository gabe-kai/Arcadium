# Database Migrations

This directory contains Flask-Migrate (Alembic) migration files for the Wiki Service database schema.

## Setup

### Prerequisites

**Important**: The PostgreSQL database must exist before running migrations. Migrations create tables, indexes, and constraints within an existing database, but do not create the database itself.

**Create the database first:**
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create the wiki database
CREATE DATABASE arcadium_wiki;
```

Or using command line:
```bash
psql -U postgres -c "CREATE DATABASE arcadium_wiki;"
```

### Initialize Migrations

Migrations are automatically initialized when you run:
```bash
flask db init
```

**Note**: This only needs to be run once per project. It creates the `migrations/` directory structure.

## Running Migrations

### Apply all pending migrations:
```bash
flask db upgrade
```

This will:
1. Create all tables (pages, comments, page_links, index_entries, page_versions, images, page_images, wiki_config, oversized_page_notifications)
2. Create all indexes (standard, partial, and composite indexes)
3. Set up foreign keys and constraints
4. Create the `alembic_version` table to track migration state

### Apply migrations up to a specific revision:
```bash
flask db upgrade <revision>
```

### Rollback to a previous revision:
```bash
flask db downgrade <revision>
```

### Rollback one revision:
```bash
flask db downgrade -1
```

## Creating New Migrations

### Auto-generate migration from model changes:
```bash
flask db migrate -m "Description of changes"
```

This will:
1. Compare current models with database schema
2. Generate a migration file in `versions/` directory
3. Review the generated migration before applying

### Review generated migration:
Always review the generated migration file before applying:
```bash
# Check the generated file
cat migrations/versions/XXXX_description.py
```

### Apply the new migration:
```bash
flask db upgrade
```

## Migration Files

- `001_initial_migration.py` - Initial database schema with all tables and indexes

## Indexes

The initial migration includes all indexes specified in the architecture documentation:

### Pages Table
- `idx_pages_parent` - Foreign key index
- `idx_pages_section` - Section grouping
- `idx_pages_slug` - Unique slug lookup
- `idx_pages_status` - Status filtering
- `idx_pages_orphaned` - Partial index (WHERE is_orphaned = TRUE)
- `idx_pages_system` - Partial index (WHERE is_system_page = TRUE)

### Comments Table
- `idx_comments_page` - Page foreign key
- `idx_comments_parent` - Parent comment foreign key
- `idx_comments_depth` - Thread depth filtering

### Page Links Table
- `idx_links_from` - Outgoing links
- `idx_links_to` - Incoming links (backlinks)

### Index Entries Table
- `idx_index_term` - Term lookup
- `idx_index_page` - Page foreign key
- `idx_index_keyword` - Partial index (WHERE is_keyword = TRUE)
- `idx_index_manual` - Partial index (WHERE is_manual = TRUE)

### Page Versions Table
- `idx_versions_page` - Page foreign key
- `idx_versions_version` - Composite index (page_id, version DESC)

### Oversized Page Notifications Table
- `idx_oversized_page` - Page foreign key
- `idx_oversized_resolved` - Resolution status
- `idx_oversized_due_date` - Due date filtering

### Images Table
- `idx_images_uuid` - UUID lookup

### Page Images Table
- `idx_page_images_page` - Page foreign key
- `idx_page_images_image` - Image foreign key

## Connection Pooling

Database connection pooling is configured in `config.py` via `SQLALCHEMY_ENGINE_OPTIONS`:

- **Pool Size**: 10 connections (default)
- **Max Overflow**: 20 additional connections (default)
- **Pool Timeout**: 30 seconds (default)
- **Pool Recycle**: 3600 seconds (1 hour, default)
- **Pool Pre-ping**: Enabled (prevents stale connections)

These can be configured via environment variables:
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT`
- `DB_POOL_RECYCLE`
- `DB_ECHO` (set to 'true' to log SQL queries)

## Troubleshooting

### Migration conflicts
If you have conflicts between migrations:
```bash
# Check current revision
flask db current

# Check migration history
flask db history

# Merge branches if needed
flask db merge -m "Merge branches"
```

### Database connection errors
Ensure `DATABASE_URL` is set correctly in your `.env` file:
```
# Option 1: Using arcadium_user and arcadium_pass (recommended)
arcadium_user=your-database-username
arcadium_pass=your-database-password
DB_NAME=arcadium_wiki

# Option 2: Using DATABASE_URL directly
DATABASE_URL=postgresql://username:password@host:port/database
```

### Stale migration state
If migrations seem out of sync:
```bash
# Check current database state
flask db current

# Stamp database with current revision (if needed)
flask db stamp head
```

## Best Practices

1. **Always review** generated migrations before applying
2. **Test migrations** on a development database first
3. **Backup database** before running migrations in production
4. **One logical change per migration** - don't combine unrelated changes
5. **Use descriptive messages** when creating migrations
6. **Never edit applied migrations** - create new migrations to fix issues
