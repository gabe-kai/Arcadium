# Auth Service

Authentication and user management service for Arcadium.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://user:pass@localhost:5432/arcadium_auth`)
  - OR use `arcadium_user` and `arcadium_pass` (will construct DATABASE_URL automatically)
  - Database name defaults to `arcadium_auth` (uses `arcadium_` prefix)
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing secret key

**Database Credentials:**
- Use `arcadium_user` and `arcadium_pass` environment variables (recommended)
- These variables are used across all Arcadium services for consistency
- The user has full permissions to do anything in the database

3. **Create database and schema:**
```sql
CREATE DATABASE arcadium_auth;
\c arcadium_auth
CREATE SCHEMA auth;
```

4. **Run migrations:**
```bash
# Set Flask app
export FLASK_APP=app  # Linux/Mac
set FLASK_APP=app     # Windows

# Create initial migration (if not exists)
flask db migrate -m "Initial schema"

# Apply migrations
flask db upgrade
```

5. **Start the service:**
```bash
flask run --port 8000
```

The service will be available at `http://localhost:8000` by default.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user (first user becomes admin)
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/verify` - Verify authentication token
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (invalidate token)
- `POST /api/auth/revoke` - Revoke token(s)

### User Management
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile
- `GET /api/users/username/{username}` - Get user by username
- `PUT /api/users/{user_id}/role` - Update user role (admin only)
- `GET /api/users` - List users (admin only)
- `POST /api/users/system` - Create system user (service token required)

## Database Schema

All tables are in the `auth` schema:
- `auth.users` - User accounts
- `auth.token_blacklist` - Revoked tokens
- `auth.password_history` - Password history for reuse prevention
- `auth.refresh_tokens` - Refresh tokens for token renewal

## Testing

```bash
# Set test environment
export FLASK_ENV=testing
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly: export TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/arcadium_testing_auth

# Run tests
pytest
```

## Documentation

- [Auth Service Specification](../../docs/services/auth-service.md)
- [Auth Service API](../../docs/api/auth-api.md)
- [Implementation Guide](../../docs/auth-service-implementation-guide.md)

