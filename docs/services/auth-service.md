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

### Shared Authentication Library

Both Auth Service and consuming services use shared code from `shared/auth/`:
- Token generation utilities
- Token validation functions
- Permission checking helpers
- JWT handling

## API Endpoints

See [Auth Service API Documentation](../api/auth-api.md) for complete endpoint specifications.

### Key Endpoints

- `POST /api/auth/register` - User registration (first user becomes admin)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout (invalidates token)
- `POST /api/auth/verify` - Token validation
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/revoke` - Revoke token (add to blacklist)
- `GET /api/users/{user_id}` - Get user profile
- `GET /api/users/username/{username}` - Get user by username
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

## Security Considerations

### Password Security
- Passwords hashed using bcrypt (12 rounds)
- Never store plaintext passwords
- **Password Requirements**:
  - Minimum length: 8 characters
  - Must contain: uppercase, lowercase, number
  - Recommended: special character
  - Cannot be common password (check against common password list)
  - Password history: Cannot reuse last 3 passwords

### JWT Tokens
- Secure secret key for signing (stored in environment variable)
- **Token Expiration**:
  - Access token: 1 hour
  - Refresh token: 7 days
  - Tokens can be refreshed before expiration
- Refresh token support with `/api/auth/refresh` endpoint
- Token revocation via blacklist (stored in database)

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
- **Login Endpoints**: 5 attempts per 15 minutes per IP
- **Registration**: 3 registrations per hour per IP
- **Token Refresh**: 10 requests per hour per user
- **Password Reset**: 3 requests per hour per email
- Rate limit headers included in responses

### Session Management
- Stateless authentication (JWT-based)
- No server-side session storage
- Multiple concurrent sessions per user allowed
- Client tracks active sessions
- On token expiration or logout: User remains on current page, UI updates to reflect unauthenticated state

## Service Architecture

### Technology Stack
- **Language**: Python/Flask (matches other services)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt

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
    services/
      auth_service.py
      token_service.py
      password_service.py
    utils/
      validators.py
  tests/
  requirements.txt
  Dockerfile
  README.md
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
