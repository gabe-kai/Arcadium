# Database Configuration

This document describes how database configuration works across services in the Arcadium monorepo.

## Overview

Each service in the Arcadium project can be configured to use its own database. By default, services use PostgreSQL for production and development, with SQLite available for testing.

## Configuration Method

Database configuration is done via environment variables. Each service reads its database connection string from a `DATABASE_URL` environment variable.

### Environment Variable Format

```
DATABASE_URL=postgresql://username:password@host:port/database
```

### Example

```
DATABASE_URL=postgresql://postgres:Le555ecure@localhost:5432/wiki
```

## Service-Specific Configuration

### Wiki Service

**Default Development Database:**
- Host: `localhost`
- Port: `5432`
- Username: `postgres`
- Password: `Le555ecure` (configurable)
- Database: `wiki`

**Configuration File:** `services/wiki/config.py`

**Environment Variables:**
- `DATABASE_URL` - Full PostgreSQL connection string
- `TEST_DATABASE_URL` - Test database connection (defaults to SQLite in-memory)

**Example `.env` file:**
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://postgres:Le555ecure@localhost:5432/wiki

# Test Database (optional, defaults to SQLite)
TEST_DATABASE_URL=postgresql://postgres:Le555ecure@localhost:5432/wiki_test
```

## Database Setup

### Creating Databases

For each service, create a dedicated PostgreSQL database:

```sql
-- Wiki service database
CREATE DATABASE wiki;

-- Wiki test database (optional)
CREATE DATABASE wiki_test;
```

### Using psql

Connect to PostgreSQL using:
```bash
psql -U postgres -d postgres
```

Default credentials:
- Username: `postgres`
- Password: `Le555ecure` (configurable per environment)

## Testing Configuration

By default, tests use SQLite in-memory databases for faster execution. To use PostgreSQL for testing, set the `TEST_DATABASE_URL` environment variable.

## Production Configuration

In production, use environment-specific `.env` files or a secrets management system. Never commit production database credentials to version control.

## Future Services

When adding new services:

1. Create a dedicated database for the service
2. Add `DATABASE_URL` configuration to the service's config file
3. Document the service's database requirements in its README
4. Update this document with service-specific details

## Security Considerations

- Never commit `.env` files containing real credentials
- Use different passwords for development, staging, and production
- Rotate database passwords regularly
- Use connection pooling in production
- Consider using SSL/TLS for database connections in production

