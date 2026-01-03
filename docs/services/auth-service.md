# Auth Service Specification

## Overview

The Auth Service provides centralized authentication and authorization for all Arcadium services. It manages user accounts, JWT token generation and validation, role-based access control, and user profile management.

## Core Responsibilities

1. **User Authentication**
   - User registration
   - Login/logout
   - Password management
   - Session management

2. **Authorization**
   - JWT token generation
   - Token validation
   - Role-based access control (RBAC)
   - Permission checking

3. **User Management**
   - User profiles
   - Role assignment
   - User lookup

## User Roles

### Role Definitions

- **viewer**: Unregistered users, read-only access to public content
- **player**: Registered users, can view and comment
- **writer**: Can create and edit content
- **admin**: Full access, can manage users and system settings

### Role Hierarchy

```
admin > writer > player > viewer
```

## Integration Points

### Wiki Service Integration

The Wiki Service depends on Auth Service for:

1. **JWT Token Validation**
   - All authenticated wiki endpoints validate tokens
   - Use shared validation library or `/api/auth/verify` endpoint

2. **User Role Checking**
   - Wiki checks user roles for permission enforcement
   - Roles determine: view, comment, edit, delete, admin access

3. **User Profile Lookup**
   - Display user information in comments, page metadata
   - Show author names, usernames

4. **Admin User for AI Content**
   - Wiki sync utility needs to find/create "admin" system user
   - AI-written pages assigned to admin user
   - **Current Implementation**: Wiki uses config-based admin user ID (`SYNC_ADMIN_USER_ID` or default UUID)
   - **Future**: `POST /api/users/system` endpoint for system user creation (not yet implemented)

### Shared Authentication Library

Both Auth Service and consuming services use shared code from `shared/auth/` for consistent authentication and authorization logic across services.

**Location:** `shared/auth/`

**Components:**

1. **Token Validation Utilities** (`shared/auth/tokens/`)
   - `validate_jwt_token(token, secret, algorithm)` - Validate and decode JWT tokens
   - `decode_token(token, secret, algorithm)` - Decode tokens without validation (for inspection)
   - `is_token_expired(token_payload)` - Check if token is expired
   - `get_token_user_id(token_payload)` - Extract user ID from token payload
   - `get_token_role(token_payload)` - Extract role from token payload

2. **Permission Checking Utilities** (`shared/auth/permissions/`)
   - `ROLE_HIERARCHY` - Role hierarchy constant (viewer: 0, player: 1, writer: 2, admin: 3)
   - `has_role(user_role, required_role)` - Check if user role meets or exceeds required role
   - `has_permission(user_role, permission)` - Check if user has specific permission (maps to role requirements)
   - `can_access_resource(user_role, resource_role)` - Check if user can access resource based on minimum role

3. **Service Token Utilities** (`shared/auth/tokens/service_tokens.py`)
   - `validate_service_token(token, secret, algorithm)` - Validate service-to-service tokens
   - `get_service_name(token_payload)` - Extract service name from service token
   - `get_service_id(token_payload)` - Extract service ID from service token
   - `is_service_token(token_payload)` - Check if token is a service token (type="service")

**Usage:**
Services import from `shared.auth.tokens` and `shared.auth.permissions` to validate tokens and check permissions without duplicating code.

**Documentation:**
- `shared/auth/tokens/README.md` - Token validation usage examples
- `shared/auth/permissions/README.md` - Permission checking usage examples

## Token Configuration

### Token Expiration
- **Access Token**: 1 hour (3600 seconds) - configurable via `JWT_ACCESS_TOKEN_EXPIRATION`
- **Refresh Token**: 7 days (604800 seconds) - configurable via `JWT_REFRESH_TOKEN_EXPIRATION`
- **Service Token**: 90 days (7776000 seconds) - configurable via `JWT_SERVICE_TOKEN_EXPIRATION`

### Token Refresh
- Tokens can be refreshed before expiration using refresh token
- When refresh token expires, user must login again
- Refresh tokens are stored in database and can be revoked

## Password Requirements

### Password Strength
- **Minimum length**: 8 characters (configurable via `PASSWORD_MIN_LENGTH`)
- **Required**: Uppercase letter, lowercase letter, number
- **Recommended**: Special character (not required)

### Password History
- Cannot reuse last 3 passwords (configurable via `PASSWORD_HISTORY_COUNT`)
- Password history is tracked in `password_history` table
- Password expiration not implemented

## API Endpoints

See [Auth Service API Documentation](../api/auth-api.md) for complete endpoint specifications.

### Key Endpoints

**Implemented:**
- `POST /api/auth/register` - User registration (first user becomes admin)
- `POST /api/auth/login` - User login
- `POST /api/auth/verify` - Token validation
- `POST /api/auth/refresh` - Refresh access token using refresh token
- `POST /api/auth/logout` - User logout (invalidates token via blacklist)
- `POST /api/auth/revoke` - Revoke token (add to blacklist)
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile
- `GET /api/users/username/{username}` - Get user by username
- `GET /api/users` - List all users (admin only)
- `PUT /api/users/{user_id}/role` - Update user role (admin only)
- `POST /api/users/system` - Create system user (service token required)

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'player',
    is_system_user BOOLEAN DEFAULT FALSE,
    is_first_user BOOLEAN DEFAULT FALSE,  -- First registered user
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email_verified ON users(email_verified);
```

### Token Blacklist Table
```sql
CREATE TABLE token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_id VARCHAR(255) NOT NULL,  -- JWT jti (JWT ID) claim
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_blacklist_token ON token_blacklist(token_id);
CREATE INDEX idx_blacklist_expires ON token_blacklist(expires_at);
```

### Password History Table
```sql
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_password_history_user ON password_history(user_id, created_at DESC);
```

### Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
```

## Security Considerations

### Password Security
- Passwords hashed using bcrypt (12 rounds, configurable via `BCRYPT_ROUNDS`)
- Never store plaintext passwords
- **Password Requirements**:
  - Minimum length: 8 characters (configurable via `PASSWORD_MIN_LENGTH`)
  - Must contain: uppercase letter, lowercase letter, number
  - Recommended: special character (not required)
  - Password history: Cannot reuse last 3 passwords (configurable via `PASSWORD_HISTORY_COUNT`)
  - Password expiration: Not implemented (no expiration requirement)

### JWT Tokens
- Secure secret key for signing (stored in environment variable)
- **Token Expiration**:
  - Access token: 1 hour (3600 seconds) - configurable via `JWT_ACCESS_TOKEN_EXPIRATION`
  - Refresh token: 7 days (604800 seconds) - configurable via `JWT_REFRESH_TOKEN_EXPIRATION`
  - Tokens can be refreshed before expiration using refresh token
- **Token Management**:
  - Refresh token support - implemented with database storage
  - Token revocation via blacklist (stored in database) - implemented
  - Logout functionality - implemented (adds token to blacklist)
  - Token blacklist checked during token verification
  - Refresh tokens stored in database with expiration tracking

### Service Tokens
- Service tokens are long-lived JWT tokens with special claims
- Format: JWT with `service_id` and `service_name` claims
- Expiration: 90 days (longer than user tokens)
- Generated by Auth Service during service setup
- Stored in service environment variables
- Validated by Auth Service or shared validation library

### Role Management
- **First User**: Automatically assigned admin role on registration
- **Subsequent Users**: Default to "player" role
- Only admins can change user roles
- System users (like "admin" for wiki) are protected
- Role changes are logged

### Rate Limiting

Rate limiting is implemented using Flask-Limiter to prevent abuse and protect against brute-force attacks.

**Implementation:**
- Library: Flask-Limiter
- Storage: Configurable via `RATELIMIT_STORAGE_URL` (default: `memory://` for development)
- Configuration: Enabled/disabled via `RATELIMIT_ENABLED` environment variable
- Error Response: JSON format with 429 status code

**Rate Limits:**
- **Login Endpoint** (`POST /api/auth/login`): 5 attempts per 15 minutes per IP address
- **Registration Endpoint** (`POST /api/auth/register`): 3 registrations per hour per email address
- **Token Refresh Endpoint** (`POST /api/auth/refresh`): 10 requests per hour per IP address

**Rate Limiting Key Functions:**
- Login/Refresh: Uses IP address (`get_remote_address`)
- Registration: Uses email address from request body (falls back to IP if email not present)

**Testing:**
- Rate limiting is disabled by default in testing configuration
- Can be explicitly enabled for integration tests via environment variable

### Security Headers

Security headers are automatically added to all HTTP responses via middleware.

**Implemented Headers:**
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering in browsers
- `Strict-Transport-Security` - Only added in production with HTTPS (max-age=31536000; includeSubDomains)

**Implementation:**
- Middleware function: `app.middleware.security.add_security_headers`
- Applied via Flask's `after_request` hook to all responses
- HSTS header only added when `request.is_secure` is True and not in debug mode

### Session Management
- Stateless authentication (JWT-based)
- No server-side session storage
- Multiple concurrent sessions per user allowed
- Client tracks active sessions
- On token expiration or logout: User remains on current page, UI updates to reflect unauthenticated state

## Service Architecture

### Technology Stack
- **Language**: Python/Flask (matches other services)
- **Database**: PostgreSQL (with Flask-SQLAlchemy and Flask-Migrate)
- **Authentication**: JWT (JSON Web Tokens) using PyJWT
- **Password Hashing**: bcrypt
- **Rate Limiting**: Flask-Limiter
- **CORS**: Flask-CORS

### Service Structure
```
services/auth/
  app/
    __init__.py
    routes/
      auth_routes.py
      user_routes.py
    models/
      user.py
      refresh_token.py
      token_blacklist.py
      password_history.py
    services/
      auth_service.py
      token_service.py
      password_service.py
    middleware/
      auth.py          # Authentication/authorization decorators
      security.py      # Security headers middleware
    utils/
      validators.py
  tests/
  config.py
  requirements.txt
  Dockerfile
  README.md
```

### Middleware and Decorators

**Authentication/Authorization Middleware** (`app.middleware.auth`):

- `@require_auth` - Requires valid JWT token in Authorization header
- `@require_role(required_role: str)` - Requires user role meets or exceeds required role
- `@require_admin` - Requires admin role
- `@require_service_token` - Requires valid service token (not user JWT)

**Usage Example:**
```python
from app.middleware.auth import require_auth, require_role, require_admin

@require_auth
def get_profile():
    # Requires authentication
    pass

@require_role("writer")
def edit_content():
    # Requires writer role or higher
    pass

@require_admin
def manage_users():
    # Requires admin role
    pass
```

## Registration Flow

### First User (Admin)
1. First user to register automatically receives admin role
2. No email verification required for first user
3. `is_first_user` flag set to `true`
4. Can immediately promote other users to admin

### Subsequent Users
1. Default role: "player"
2. Email verification required (verification email sent)
3. Account limited until email verified
4. Must be promoted to writer/admin by existing admin

## Logout and Token Management

### Logout
- `POST /api/auth/logout` endpoint
- Adds token to blacklist
- Client should delete token from storage
- User remains on current page, UI automatically updates to reflect unauthenticated state (permission-based buttons disappear)

### Token Revocation
- `POST /api/auth/revoke` endpoint
- Revoke specific token (by token ID)
- Revoke all user tokens (admin only)
- Tokens added to blacklist until expiration
- Blacklist checked on every token validation

## Future Enhancements

- OAuth2 integration
- Two-factor authentication (2FA)
- Password reset via email
- Account lockout after failed attempts
- Audit logging for security events
- Session management dashboard
