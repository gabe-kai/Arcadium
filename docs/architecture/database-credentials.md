# Database Credentials Configuration

## Overview

All Arcadium services use consistent database credentials via environment variables `arcadium_user` and `arcadium_pass`. This ensures consistency across the entire project and simplifies configuration management.

## Environment Variables

### Primary Method (Recommended)

Use `arcadium_user` and `arcadium_pass` environment variables:

```bash
arcadium_user=your-database-username
arcadium_pass=your-database-password
DB_HOST=localhost      # Optional, defaults to localhost
DB_PORT=5432           # Optional, defaults to 5432
DB_NAME=service-name    # Optional, service-specific default
```

Services will automatically construct the `DATABASE_URL` from these variables.

### Alternative Method

You can also set `DATABASE_URL` directly:

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

## Service-Specific Configuration

### Wiki Service
- Default database: `arcadium_wiki`
- Set `DB_NAME=arcadium_wiki` or use default
- Test database: `arcadium_testing_wiki`

### Auth Service
- Default database: `arcadium_auth`
- Set `DB_NAME=arcadium_auth` or use default
- Test database: `arcadium_testing_auth`

### Game Server
- Default database: `arcadium_game_server`
- Set `DB_NAME=arcadium_game_server` or use default
- Test database: `arcadium_testing_game_server`

### Database Naming Convention

All databases use the `arcadium_` prefix:
- **Production/Development**: `arcadium_<service_name>`
- **Testing**: `arcadium_testing_<service_name>`

This makes it clear which databases belong to the Arcadium project and prevents conflicts with other projects.

## Setting Environment Variables

### Windows (PowerShell)
```powershell
$env:arcadium_user = "your-username"
$env:arcadium_pass = "your-password"
```

### Windows (Command Prompt)
```cmd
set arcadium_user=your-username
set arcadium_pass=your-password
```

### Linux/Mac (Bash)
```bash
export arcadium_user=your-username
export arcadium_pass=your-password
```

### Using .env Files

Create a `.env` file in each service directory:

```bash
# .env
arcadium_user=your-username
arcadium_pass=your-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=service-name
```

The `.env` file will be automatically loaded by services using `python-dotenv`.

## Security Considerations

1. **Never commit `.env` files** containing real credentials to version control
2. **Use different passwords** for development, staging, and production
3. **Rotate passwords regularly** in production environments
4. **Use secrets management** in production (e.g., AWS Secrets Manager, HashiCorp Vault)
5. **Limit access** to the `arcadium_user` credentials

## Migration from Old Configuration

If you were previously using hardcoded credentials or different variable names:

1. Set `arcadium_user` and `arcadium_pass` environment variables
2. Remove any hardcoded credentials from configuration files
3. Update `.env` files to use the new variables
4. Services will automatically use the new variables

## Testing

For test databases, services will automatically construct `TEST_DATABASE_URL` from `arcadium_user` and `arcadium_pass` if not explicitly set:

```bash
# Test database URL will be: postgresql://arcadium_user:arcadium_pass@localhost:5432/arcadium_testing_<service_name>
# Example: postgresql://arcadium_user:arcadium_pass@localhost:5432/arcadium_testing_wiki
```

All test databases use the `arcadium_testing_` prefix to clearly identify them as test databases.

You can also set `TEST_DATABASE_URL` explicitly if needed.

## Troubleshooting

### Connection Errors

If you get connection errors:
1. Verify `arcadium_user` and `arcadium_pass` are set correctly
2. Check that PostgreSQL is running
3. Verify the user exists and has correct permissions
4. Check `DB_HOST` and `DB_PORT` if using non-default values

### Permission Errors

If you get permission errors:
1. Verify the `arcadium_user` has the required permissions
2. Check that the database exists
3. Verify the user can connect to PostgreSQL

## See Also

- [Database Configuration](database-configuration.md) - General database setup
- Service-specific README files for service-specific database requirements
