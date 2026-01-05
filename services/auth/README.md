# Auth Service

Authentication and user management service for Arcadium.

## Setup

1. **Install dependencies:**
```bash
# From project root (installs shared dependencies)
pip install -r requirements.txt

# From services/auth (installs auth-specific dependencies)
cd services/auth
pip install -r requirements.txt
```

**Note:** The root `requirements.txt` contains shared dependencies (Flask, SQLAlchemy, psycopg2-binary, etc.). The service-specific `requirements.txt` only contains auth-specific packages (PyJWT, bcrypt, Flask-Limiter, etc.).

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

The Auth Service has comprehensive test coverage with 192 tests organized into the following test suites:

### Test Organization

- **`tests/test_services/`** - Unit tests for service layer
  - `test_password_service.py` - PasswordService tests (20 tests)
  - `test_token_service.py` - TokenService tests (20 tests)
  - `test_auth_service.py` - AuthService tests (23 tests)

- **`tests/test_models/`** - Unit tests for database models
  - `test_user_model.py` - User model tests (13 tests)
  - `test_refresh_token_model.py` - RefreshToken model tests (6 tests)
  - `test_token_blacklist_model.py` - TokenBlacklist model tests (4 tests)
  - `test_password_history_model.py` - PasswordHistory model tests (4 tests)

- **`tests/test_utils/`** - Unit tests for utility functions
  - `test_validators.py` - Validator tests (33 tests)

- **`tests/test_integration/`** - Integration tests for complete user flows
  - `test_auth_flows.py` - Full authentication and user management flows (10 tests)

- **`tests/test_api/`** - API endpoint tests
  - Token management endpoints (Phase 3: 16 tests)
  - User management endpoints (Phase 4: 27 tests)
  - Rate limiting and security headers (Phase 5: 14 tests)

### Running Tests

```bash
# Set test environment
export FLASK_ENV=testing
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly: export TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/arcadium_testing_auth

# Run all tests
cd services/auth
pytest

# Run specific test suite
pytest tests/test_services/        # Service layer tests
pytest tests/test_models/          # Model tests
pytest tests/test_utils/           # Validator tests
pytest tests/test_integration/     # Integration tests
pytest tests/test_api/             # API endpoint tests

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Status

- **Total Tests**: 192 tests
- **Passing**: 136 tests
- **Known Issues**: ~56 tests with session isolation, timezone comparison, and blacklist verification issues (to be fixed in cleanup round)

## Documentation

- [Auth Service Specification](../../docs/services/auth-service.md)
- [Auth Service API](../../docs/api/auth-api.md)
- [Implementation Guide](../../docs/auth-service-implementation-guide.md)
