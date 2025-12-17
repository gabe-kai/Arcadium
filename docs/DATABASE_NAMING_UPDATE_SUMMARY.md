# Database Naming Convention Update Summary

## Overview

All Arcadium databases have been updated to use the `arcadium_` prefix for clear identification and to prevent conflicts with other projects on the same PostgreSQL instance.

## New Naming Convention

### Production/Development Databases
- **Pattern**: `arcadium_<service_name>`
- **Examples**:
  - `arcadium_wiki` - Wiki Service
  - `arcadium_auth` - Auth Service
  - `arcadium_game_server` - Game Server
  - `arcadium_presence` - Presence Service
  - `arcadium_chat` - Chat Service
  - `arcadium_leaderboard` - Leaderboard Service
  - `arcadium_assets` - Assets Service
  - `arcadium_admin` - Admin Service

### Test Databases
- **Pattern**: `arcadium_testing_<service_name>`
- **Examples**:
  - `arcadium_testing_wiki` - Wiki Service test database
  - `arcadium_testing_auth` - Auth Service test database
  - `arcadium_testing_game_server` - Game Server test database

## Files Updated

### Configuration Files
- ✅ `services/auth/config.py` - Default: `arcadium_auth`, Test: `arcadium_testing_auth`
- ✅ `services/wiki/config.py` - Default: `arcadium_wiki`, Test: `arcadium_testing_wiki`
- ✅ `services/wiki/tests/conftest.py` - Test DB: `arcadium_testing_wiki`
- ✅ `services/auth/scripts/setup_database.py` - Default: `arcadium_auth`
- ✅ `docker-compose.yml` - All services updated to use `arcadium_*` databases
- ✅ `infrastructure/scripts/migrate.sh` - Default: `arcadium_wiki`

### Documentation Files
- ✅ `docs/architecture/database-configuration.md` - Complete update
- ✅ `docs/architecture/database-credentials.md` - Updated with new names
- ✅ `docs/architecture/database-naming-convention.md` (NEW) - Comprehensive guide
- ✅ `docs/DATABASE_MIGRATION_GUIDE.md` (NEW) - Migration instructions
- ✅ `docs/ci-cd.md` - All test database references updated
- ✅ `README.md` - Database creation examples updated
- ✅ `services/auth/README.md` - Database setup instructions updated
- ✅ `services/wiki/README.md` - Test database references updated
- ✅ `services/wiki/migrations/README.md` - Database creation examples updated
- ✅ `services/game-server/README.md` - Database name updated
- ✅ `docs/wiki-service-specification.md` - Database creation updated
- ✅ `docs/wiki-implementation-guide.md` - Test database name updated
- ✅ `docs/auth-service-implementation-guide.md` - Database names updated
- ✅ `docs/services/service-architecture.md` - Database examples updated
- ✅ `.github/workflows/wiki-service-tests.yml` - Test database name updated

### Scripts
- ✅ `scripts/drop_arcadium_databases.py` (NEW) - Drops all `arcadium_*` databases

## Migration Steps

### Step 1: Drop Old Databases

```bash
# Use the drop script
python scripts/drop_arcadium_databases.py --yes

# Or manually via psql
psql -U $arcadium_user -d postgres
DROP DATABASE IF EXISTS wiki;
DROP DATABASE IF EXISTS wiki_test;
DROP DATABASE IF EXISTS auth;
DROP DATABASE IF EXISTS auth_test;
```

### Step 2: Create New Databases

```sql
-- Production/Development
CREATE DATABASE arcadium_wiki;
CREATE DATABASE arcadium_auth;

-- Test databases
CREATE DATABASE arcadium_testing_wiki;
CREATE DATABASE arcadium_testing_auth;
```

### Step 3: Run Migrations

```bash
# Auth Service
cd services/auth
set FLASK_APP=app
set DB_NAME=arcadium_auth
flask db migrate -m "Initial schema"  # If needed
flask db upgrade

# Wiki Service
cd services/wiki
set FLASK_APP=app
set DB_NAME=arcadium_wiki
flask db upgrade
```

## Verification

Check that databases were created:

```sql
SELECT datname FROM pg_database 
WHERE datname LIKE 'arcadium_%' 
ORDER BY datname;
```

Expected databases:
- `arcadium_auth`
- `arcadium_wiki`
- `arcadium_testing_wiki` (created when tests run)
- `arcadium_testing_auth` (created when tests run)

## Benefits

1. **Clear Identification**: Immediately obvious which databases belong to Arcadium
2. **Conflict Prevention**: Won't conflict with other projects' databases
3. **Easy Management**: Can list all Arcadium databases with a simple query
4. **Test Isolation**: Test databases clearly separated with `arcadium_testing_` prefix
5. **Consistency**: Same naming pattern across all services

## See Also

- [Database Naming Convention](architecture/database-naming-convention.md)
- [Database Migration Guide](DATABASE_MIGRATION_GUIDE.md)
- [Database Configuration](architecture/database-configuration.md)
