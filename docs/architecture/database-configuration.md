# Database Configuration

This document describes how database configuration works across services in the Arcadium monorepo.

## Overview

Each service in the Arcadium project can be configured to use its own database. By default, services use PostgreSQL for production and development, with SQLite available for testing.

## Configuration Method

Database configuration is done via environment variables. Each service can use either:
1. A `DATABASE_URL` environment variable with the full connection string, OR
2. `arcadium_user` and `arcadium_pass` environment variables (recommended for consistency)

### Environment Variable Format

**Option 1: Full Connection String**
```
DATABASE_URL=postgresql://username:password@host:port/database
```

**Option 2: Individual Variables (Recommended)**
```
arcadium_user=your-database-username
arcadium_pass=your-database-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=service-name
```

The `arcadium_user` and `arcadium_pass` variables are used across all Arcadium services for consistency. The user has full permissions to do anything in the database.

### Example

```
# Using arcadium_user and arcadium_pass (recommended)
arcadium_user=arcadium
arcadium_pass=your-secure-password
DB_NAME=arcadium_wiki  # All databases use arcadium_ prefix

# Or using DATABASE_URL directly
DATABASE_URL=postgresql://arcadium:your-secure-password@localhost:5432/arcadium_wiki
```

### Database Naming Convention

**All databases use the `arcadium_` prefix** to clearly identify them as part of the Arcadium project:

- **Production/Development databases**: `arcadium_<service_name>`
  - Examples: `arcadium_wiki`, `arcadium_auth`, `arcadium_game_server`
  
- **Test databases**: `arcadium_testing_<service_name>`
  - Examples: `arcadium_testing_wiki`, `arcadium_testing_auth`, `arcadium_testing_game_server`

This naming convention:
- Makes it clear which databases belong to the Arcadium project
- Prevents conflicts with other projects on the same PostgreSQL instance
- Organizes test databases separately from production/development databases

## Service-Specific Configuration

### Wiki Service

**Default Development Database:**
- Host: `localhost` (configurable via `DB_HOST`)
- Port: `5432` (configurable via `DB_PORT`)
- Username: Set via `arcadium_user` environment variable
- Password: Set via `arcadium_pass` environment variable
- Database: `arcadium_wiki` (configurable via `DB_NAME`, defaults to `arcadium_wiki`)

**Configuration File:** `services/wiki/config.py`

**Environment Variables:**
- `DATABASE_URL` - Full PostgreSQL connection string (optional if using arcadium_user/arcadium_pass)
- `arcadium_user` - Database username (used across all services)
- `arcadium_pass` - Database password (used across all services)
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: arcadium_wiki)
- `TEST_DATABASE_URL` - Test database connection (optional, defaults to constructed from arcadium_user/arcadium_pass or SQLite)

**Example `.env` file:**
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration (Option 1: Using arcadium_user/arcadium_pass - Recommended)
arcadium_user=arcadium
arcadium_pass=your-secure-password
DB_NAME=arcadium_wiki  # Defaults to arcadium_wiki if not set

# Database Configuration (Option 2: Using DATABASE_URL directly)
# DATABASE_URL=postgresql://arcadium:your-secure-password@localhost:5432/arcadium_wiki

# Test Database (optional, will be constructed from arcadium_user/arcadium_pass if not set)
# Test databases use arcadium_testing_* prefix
# TEST_DATABASE_URL=postgresql://arcadium:your-secure-password@localhost:5432/arcadium_testing_wiki
```

## Database Setup

### Creating Databases

For each service, create a dedicated PostgreSQL database:

```sql
-- Wiki service database (production/development)
CREATE DATABASE arcadium_wiki;

-- Wiki test database
CREATE DATABASE arcadium_testing_wiki;
```

### Using psql

Connect to PostgreSQL using:
```bash
# Using arcadium_user and arcadium_pass
psql -U $arcadium_user -d postgres
# Or on Windows:
psql -U %arcadium_user% -d postgres
```

Credentials:
- Username: Set via `arcadium_user` environment variable
- Password: Set via `arcadium_pass` environment variable
- The user has full permissions to do anything in the database

## Testing Configuration

By default, tests use SQLite in-memory databases for faster execution. To use PostgreSQL for testing, set the `TEST_DATABASE_URL` environment variable.

## Production Configuration

In production, use environment-specific `.env` files or a secrets management system. Never commit production database credentials to version control.

## Future Services

When adding new services:

1. Create a dedicated database for the service using the `arcadium_` prefix
   - Production/development: `arcadium_<service_name>`
   - Testing: `arcadium_testing_<service_name>`
2. Add database configuration to the service's config file that supports:
   - `DATABASE_URL` (direct connection string), OR
   - `arcadium_user` and `arcadium_pass` (recommended for consistency)
3. Set default `DB_NAME` to `arcadium_<service_name>` in config
4. Document the service's database requirements in its README
5. Update this document with service-specific details
6. Use `arcadium_user` and `arcadium_pass` for consistency across all services

## Security Considerations

- Never commit `.env` files containing real credentials
- Use different passwords for development, staging, and production
- Rotate database passwords regularly (update `arcadium_pass` environment variable)
- Use connection pooling in production
- Consider using SSL/TLS for database connections in production
- The `arcadium_user` has full database permissions - use strong passwords
- Store `arcadium_user` and `arcadium_pass` securely (environment variables, secrets management)

