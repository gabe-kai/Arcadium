# Database Migration Guide: arcadium_ Prefix

## Overview

All Arcadium databases have been updated to use the `arcadium_` prefix for clear identification and to prevent conflicts with other projects.

## New Database Naming Convention

### Production/Development Databases
- Pattern: `arcadium_<service_name>`
- Examples:
  - `arcadium_wiki`
  - `arcadium_auth`
  - `arcadium_game_server`

### Test Databases
- Pattern: `arcadium_testing_<service_name>`
- Examples:
  - `arcadium_testing_wiki`
  - `arcadium_testing_auth`
  - `arcadium_testing_game_server`

## Migration Steps

### Step 1: Drop Old Databases

If you have existing databases without the `arcadium_` prefix, drop them:

```bash
# Option 1: Use the drop script (drops all arcadium_* databases)
python scripts/drop_arcadium_databases.py --yes

# Option 2: Manual drop via psql
psql -U $arcadium_user -d postgres
DROP DATABASE IF EXISTS wiki;
DROP DATABASE IF EXISTS wiki_test;
DROP DATABASE IF EXISTS auth;
DROP DATABASE IF EXISTS auth_test;
```

### Step 2: Create New Databases

Create databases with the new naming convention:

```sql
-- Production/Development databases
CREATE DATABASE arcadium_wiki;
CREATE DATABASE arcadium_auth;

-- Test databases
CREATE DATABASE arcadium_testing_wiki;
CREATE DATABASE arcadium_testing_auth;
```

Or use the setup scripts:

```bash
# Auth Service
cd services/auth
python scripts/setup_database.py --db-name arcadium_auth

# Wiki Service
cd services/wiki
python scripts/setup_database.py --db-name arcadium_wiki
```

### Step 3: Run Migrations

Run migrations for each service:

```bash
# Auth Service
cd services/auth
set FLASK_APP=app
set DB_NAME=arcadium_auth
flask db migrate -m "Initial schema"  # If migration doesn't exist
flask db upgrade

# Wiki Service
cd services/wiki
set FLASK_APP=app
set DB_NAME=arcadium_wiki
flask db upgrade
```

## Configuration Updates

All configuration files have been updated:

- ✅ `services/auth/config.py` - Default: `arcadium_auth`
- ✅ `services/wiki/config.py` - Default: `arcadium_wiki`
- ✅ `services/wiki/tests/conftest.py` - Test DB: `arcadium_testing_wiki`
- ✅ All documentation files updated

## Environment Variables

No changes needed to environment variables. Services will automatically use the new database names:

```bash
# These still work the same way
arcadium_user=your-username
arcadium_pass=your-password
DB_NAME=arcadium_wiki  # Optional, defaults to arcadium_<service>
```

## Verification

Verify databases were created:

```sql
SELECT datname FROM pg_database
WHERE datname LIKE 'arcadium_%'
ORDER BY datname;
```

You should see:
- `arcadium_auth`
- `arcadium_wiki`
- `arcadium_testing_wiki` (when tests run)
- `arcadium_testing_auth` (when tests run)

## Rollback

If you need to rollback (not recommended after migration):

1. Update config files to use old database names
2. Rename databases back:
   ```sql
   ALTER DATABASE arcadium_wiki RENAME TO wiki;
   ALTER DATABASE arcadium_testing_wiki RENAME TO wiki_test;
   ```

## See Also

- [Database Naming Convention](architecture/database-naming-convention.md)
- [Database Configuration](architecture/database-configuration.md)
