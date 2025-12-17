# Database Naming Convention

## Overview

All Arcadium databases use a consistent naming convention with the `arcadium_` prefix to clearly identify them as part of the Arcadium project. This prevents conflicts with other projects on the same PostgreSQL instance and makes database management easier.

## Naming Pattern

### Production/Development Databases

**Pattern**: `arcadium_<service_name>`

**Examples**:
- `arcadium_wiki` - Wiki Service database
- `arcadium_auth` - Auth Service database
- `arcadium_game_server` - Game Server database
- `arcadium_presence` - Presence Service database
- `arcadium_chat` - Chat Service database
- `arcadium_leaderboard` - Leaderboard Service database
- `arcadium_assets` - Assets Service database
- `arcadium_admin` - Admin Service database

### Test Databases

**Pattern**: `arcadium_testing_<service_name>`

**Examples**:
- `arcadium_testing_wiki` - Wiki Service test database
- `arcadium_testing_auth` - Auth Service test database
- `arcadium_testing_game_server` - Game Server test database

## Benefits

1. **Clear Identification**: Immediately obvious which databases belong to Arcadium
2. **Conflict Prevention**: Won't conflict with other projects' databases
3. **Easy Management**: Can easily list all Arcadium databases: `SELECT datname FROM pg_database WHERE datname LIKE 'arcadium_%'`
4. **Test Isolation**: Test databases clearly separated with `arcadium_testing_` prefix
5. **Consistency**: Same naming pattern across all services

## Configuration

### Default Database Names

Each service has a default database name in its configuration:

- **Wiki Service**: `arcadium_wiki` (configurable via `DB_NAME`)
- **Auth Service**: `arcadium_auth` (configurable via `DB_NAME`)
- **Game Server**: `arcadium_game_server` (configurable via `DB_NAME`)

### Overriding Defaults

You can override the default database name by setting `DB_NAME` environment variable:

```bash
# Use default (arcadium_wiki)
arcadium_user=arcadium
arcadium_pass=password

# Override default
arcadium_user=arcadium
arcadium_pass=password
DB_NAME=arcadium_wiki_custom
```

## Creating Databases

### Manual Creation

```sql
-- Production/Development databases
CREATE DATABASE arcadium_wiki;
CREATE DATABASE arcadium_auth;
CREATE DATABASE arcadium_game_server;

-- Test databases
CREATE DATABASE arcadium_testing_wiki;
CREATE DATABASE arcadium_testing_auth;
CREATE DATABASE arcadium_testing_game_server;
```

### Using Setup Scripts

Service-specific setup scripts will create databases with the correct naming:

```bash
# Auth Service
cd services/auth
python scripts/setup_database.py --db-name arcadium_auth

# Wiki Service
cd services/wiki
python scripts/setup_database.py --db-name arcadium_wiki
```

## Listing Arcadium Databases

To see all Arcadium databases:

```sql
SELECT datname FROM pg_database 
WHERE datname LIKE 'arcadium_%' 
ORDER BY datname;
```

This will show:
- All production/development databases (`arcadium_*`)
- All test databases (`arcadium_testing_*`)

## Migration

If you have existing databases without the `arcadium_` prefix:

1. **Option 1: Drop and recreate** (if no critical data)
   - Use `scripts/drop_arcadium_databases.py` to clean up
   - Run migrations to create new databases

2. **Option 2: Rename databases** (if you have data to preserve)
   ```sql
   ALTER DATABASE wiki RENAME TO arcadium_wiki;
   ALTER DATABASE wiki_test RENAME TO arcadium_testing_wiki;
   ```

## See Also

- [Database Configuration](database-configuration.md) - General database setup
- [Database Credentials](database-credentials.md) - Using arcadium_user and arcadium_pass
