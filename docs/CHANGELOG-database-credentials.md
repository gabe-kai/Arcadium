# Database Credentials Update

## Summary

All Arcadium services now use consistent database credentials via `arcadium_user` and `arcadium_pass` environment variables. This change provides:

- **Consistency**: Same credentials across all services
- **Simplicity**: One set of environment variables for the entire project
- **Security**: No hardcoded credentials in documentation
- **Flexibility**: Can still use `DATABASE_URL` directly if preferred

## Changes Made

### Configuration Files Updated

1. **services/auth/config.py**
   - Now constructs `DATABASE_URL` from `arcadium_user` and `arcadium_pass` if not set
   - Updated test configuration to use same variables

2. **services/wiki/config.py**
   - Now constructs `DATABASE_URL` from `arcadium_user` and `arcadium_pass` if not set
   - Updated test configuration to use same variables

### Documentation Updated

1. **docs/architecture/database-configuration.md**
   - Updated to document both methods (DATABASE_URL and arcadium_user/arcadium_pass)
   - Updated examples to use new variables
   - Added note about user permissions

2. **docs/architecture/database-credentials.md** (NEW)
   - New comprehensive guide for using arcadium_user and arcadium_pass
   - Security considerations
   - Troubleshooting guide

3. **docs/ci-cd.md**
   - Updated test database URL examples
   - Updated CI configuration examples

4. **README.md**
   - Updated database credentials section
   - Updated test examples

5. **services/auth/README.md**
   - Updated environment variable documentation
   - Added note about arcadium_user and arcadium_pass

6. **services/wiki/README.md**
   - Updated test configuration examples

7. **docs/auth-service-implementation-guide.md**
   - Updated environment variable documentation

8. **docs/wiki-implementation-guide.md**
   - Updated test configuration examples

9. **docs/services/service-architecture.md**
   - Updated database connection string examples

10. **services/wiki/migrations/README.md**
    - Updated database URL examples

11. **services/game-server/README.md**
    - Updated database configuration examples

### Scripts Updated

1. **services/auth/scripts/setup_database.py**
   - Now uses arcadium_user and arcadium_pass if DATABASE_URL not set

2. **services/wiki/tests/conftest.py**
   - Now uses arcadium_user and arcadium_pass for test database configuration

## Environment Variables

### Required (One of the following)

**Option 1: Using arcadium_user and arcadium_pass (Recommended)**
```bash
arcadium_user=your-database-username
arcadium_pass=your-database-password
DB_HOST=localhost      # Optional, defaults to localhost
DB_PORT=5432           # Optional, defaults to 5432
DB_NAME=service-name   # Optional, service-specific default
```

**Option 2: Using DATABASE_URL directly**
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

## Database User Permissions

The `arcadium_user` has **full permissions** to do anything in the database:
- CREATE, DROP, ALTER databases and schemas
- CREATE, DROP, ALTER tables
- INSERT, UPDATE, DELETE, SELECT on all tables
- CREATE, DROP indexes
- All other database operations

This is intentional for development and allows services to manage their own database schemas.

## Migration Guide

If you were using hardcoded credentials or different variable names:

1. Set `arcadium_user` and `arcadium_pass` environment variables
2. Services will automatically use these to construct `DATABASE_URL`
3. No code changes needed - configuration handles it automatically
4. Update `.env` files to use the new variables

## Backward Compatibility

- Services still support `DATABASE_URL` if set directly
- If both are set, `DATABASE_URL` takes precedence
- Existing `.env` files with `DATABASE_URL` will continue to work

## Testing

Test databases automatically use `arcadium_user` and `arcadium_pass`:
- `TEST_DATABASE_URL` will be constructed automatically if not set
- Format: `postgresql://${arcadium_user}:${arcadium_pass}@localhost:5432/service_test`
- Can still set `TEST_DATABASE_URL` explicitly if needed

## See Also

- [Database Configuration](architecture/database-configuration.md)
- [Database Credentials Guide](architecture/database-credentials.md)
