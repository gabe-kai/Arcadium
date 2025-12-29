# Auth Service Implementation Guide

## Overview

This guide provides a detailed, phased implementation plan for building the Auth Service. The service provides centralized authentication and authorization for all Arcadium services, managing user accounts, JWT token generation and validation, and role-based access control.

## Current Status

- ✅ **Design Complete**: Comprehensive specification and API documentation
- ✅ **Basic Structure**: Flask app skeleton exists
- ✅ **Phase 1 Complete**: Database setup, models, configuration
- ✅ **Phase 2 Complete**: Core authentication (register, login, verify) with UI integration
- ✅ **Database**: Set up with migrations
- ✅ **Tests**: Comprehensive test coverage (90+ client tests, backend tests in progress)

## Implementation Phases

### Phase 1: Foundation & Database Setup
**Goal**: Set up project structure, database models, and basic configuration

### Phase 2: Core Authentication (MVP)
**Goal**: Implement user registration, login, and basic token generation

### Phase 3: Token Management
**Goal**: Implement token verification, refresh, logout, and revocation

### Phase 4: User Management
**Goal**: Implement user profile endpoints and role management

### Phase 5: Security & Rate Limiting
**Goal**: Add password security, rate limiting, and token blacklist

### Phase 6: Shared Auth Library
**Goal**: Create shared authentication utilities for other services

### Phase 7: Testing & Documentation
**Goal**: Comprehensive test coverage and final documentation

---

## Phase 1: Foundation & Database Setup

### 1.1 Project Structure
**Tasks**:
- [x] Verify Flask app structure exists
- [x] Set up configuration management (`config.py`)
- [x] Set up environment variable handling (`.env.example`)
- [x] Configure database connection (PostgreSQL)
- [x] Set up Flask-Migrate for database migrations
- [x] Configure CORS for frontend integration
- [x] Set up logging configuration

**Files to Create/Modify**:
- `services/auth/config.py` - Configuration classes
- `services/auth/.env.example` - Environment variable template
- `services/auth/app/__init__.py` - Update Flask app factory
- `services/auth/requirements.txt` - Update dependencies

**Dependencies**:
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- psycopg2-binary
- python-dotenv
- PyJWT
- bcrypt
- python-dateutil

### 1.2 Database Models
**Tasks**:
- [x] Create `User` model (`app/models/user.py`)
  - Fields: id, username, email, password_hash, role, is_system_user, is_first_user, email_verified, email_verification_token, created_at, updated_at, last_login
  - Indexes: username, email, role, email_verified
  - Methods: `check_password()`, `to_dict()`, `is_admin()`, etc.
- [x] Create `TokenBlacklist` model (`app/models/token_blacklist.py`)
  - Fields: id, token_id, user_id, expires_at, created_at
  - Indexes: token_id, expires_at
- [x] Create `PasswordHistory` model (`app/models/password_history.py`)
  - Fields: id, user_id, password_hash, created_at
  - Indexes: user_id, created_at
- [x] Create `RefreshToken` model (`app/models/refresh_token.py`)
  - Fields: id, user_id, token_hash, expires_at, created_at, last_used_at
  - Indexes: user_id, token_hash, expires_at
- [ ] Update `app/models/__init__.py` to export all models

**Database Schema**:
- Schema: `auth` (separate from other services)
- Tables: `users`, `token_blacklist`, `password_history`, `refresh_tokens`

### 1.3 Database Migrations
**Tasks**:
- [ ] Create initial migration (`flask db init`)
- [ ] Create migration for all tables (`flask db migrate -m "Initial schema"`)
- [ ] Review migration file
- [ ] Test migration (`flask db upgrade`)
- [ ] Create rollback test (`flask db downgrade`)

### 1.4 Configuration
**Tasks**:
- [ ] Create development config
- [ ] Create testing config
- [ ] Create production config
- [ ] Set up environment variables:
  - `DATABASE_URL` - PostgreSQL connection string (optional)
  - `arcadium_user` - Database username (recommended, used across all services)
  - `arcadium_pass` - Database password (recommended, used across all services)
  - `DB_HOST` - Database host (default: localhost)
  - `DB_PORT` - Database port (default: 5432)
  - `DB_NAME` - Database name (default: arcadium_auth)
  - `JWT_SECRET_KEY` - Secret for JWT signing
  - `JWT_ACCESS_TOKEN_EXPIRATION` - Access token expiration (default: 3600)
  - `JWT_REFRESH_TOKEN_EXPIRATION` - Refresh token expiration (default: 604800)
  - `BCRYPT_ROUNDS` - Password hashing rounds (default: 12)
  - `FLASK_ENV` - Environment (development, testing, production)

**Deliverables**:
- ✅ Complete project structure
- ✅ Database models defined
- ✅ Initial migration created
- ✅ Configuration system working
- ✅ Environment variables documented

**Testing**:
- [ ] Test database connection
- [ ] Test model creation
- [ ] Test migration up/down

---

## Phase 2: Core Authentication (MVP)

### 2.1 Password Service
**Tasks**:
- [x] Create `app/services/password_service.py`
  - `hash_password(password: str) -> str` - Hash password with bcrypt
  - `check_password(password: str, password_hash: str) -> bool` - Verify password
  - `validate_password_strength(password: str) -> tuple[bool, str]` - Validate requirements
  - `check_password_history(user_id: UUID, password: str, max_history: int = 3) -> bool` - Check if password was recently used
  - `save_password_history(user_id: UUID, password_hash: str)` - Save to history

**Password Requirements**:
- Minimum 8 characters
- Must contain: uppercase, lowercase, number
- Recommended: special character
- Cannot reuse last 3 passwords

### 2.2 Token Service
**Tasks**:
- [x] Create `app/services/token_service.py`
  - `generate_access_token(user: User) -> str` - Generate JWT access token
  - `generate_refresh_token(user: User) -> str` - Generate refresh token
  - `verify_token(token: str) -> dict | None` - Verify and decode token
  - `is_token_blacklisted(token_id: str) -> bool` - Check blacklist
  - `blacklist_token(token_id: str, user_id: UUID, expires_at: datetime)` - Add to blacklist
  - `generate_service_token(service_name: str, service_id: str) -> str` - Generate service token

**JWT Token Structure**:
```json
{
  "user_id": "uuid",
  "username": "username",
  "role": "player",
  "jti": "token-id",
  "iat": 1234567890,
  "exp": 1234571490
}
```

### 2.3 Auth Service
**Tasks**:
- [ ] Create `app/services/auth_service.py`
  - `register_user(username: str, email: str, password: str) -> tuple[User, bool]` - Register user, return (user, is_first_user)
  - `login_user(username: str, password: str) -> tuple[User, str, str] | None` - Login, return (user, access_token, refresh_token)
  - `verify_user_token(token: str) -> dict | None` - Verify token and return user info
  - `refresh_access_token(refresh_token: str) -> tuple[str, str] | None` - Refresh access token
  - `logout_user(token: str, user_id: UUID)` - Logout (blacklist token)
  - `revoke_token(token_id: str, user_id: UUID, revoke_all: bool = False)` - Revoke token(s)

### 2.4 Validators
**Tasks**:
- [ ] Create `app/utils/validators.py`
  - `validate_username(username: str) -> tuple[bool, str]` - Validate username format
  - `validate_email(email: str) -> tuple[bool, str]` - Validate email format
  - `validate_password(password: str) -> tuple[bool, str]` - Validate password strength
  - `sanitize_username(username: str) -> str` - Sanitize username input

**Validation Rules**:
- Username: 3-100 chars, alphanumeric + underscore/hyphen
- Email: Valid email format
- Password: See password requirements above

### 2.5 Registration Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/register` in `app/routes/auth_routes.py`
  - Validate input (username, email, password)
  - Check if first user (no users in database)
  - Hash password
  - Create user (role: admin if first, player otherwise)
  - Generate tokens
  - Return user info and tokens
  - Handle errors (duplicate username/email, validation errors)

**Response**:
```json
{
  "user": {
    "id": "uuid",
    "username": "newuser",
    "email": "user@example.com",
    "role": "admin" | "player",
    "is_first_user": true | false,
    "email_verified": true | false
  },
  "token": "jwt-access-token",
  "refresh_token": "refresh-token",
  "expires_in": 3600,
  "requires_email_verification": false | true
}
```

### 2.6 Login Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/login` in `app/routes/auth_routes.py`
  - Validate input (username, password)
  - Find user by username
  - Verify password
  - Update last_login timestamp
  - Generate tokens
  - Return user info and tokens
  - Handle errors (invalid credentials, user not found)

**Response**:
```json
{
  "user": {
    "id": "uuid",
    "username": "username",
    "email": "user@example.com",
    "role": "player"
  },
  "token": "jwt-access-token",
  "refresh_token": "refresh-token",
  "expires_in": 3600
}
```

### 2.7 Verify Token Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/verify` in `app/routes/auth_routes.py`
  - Validate token format
  - Verify token signature
  - Check token expiration
  - Check token blacklist
  - Return user info and expiration
  - Handle errors (invalid token, expired, blacklisted)

**Response**:
```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "username": "username",
    "role": "player"
  },
  "expires_at": "2024-01-01T01:00:00Z"
}
```

**Deliverables**:
- ✅ User registration working
- ✅ User login working
- ✅ Token generation working
- ✅ Token verification working
- ✅ First user becomes admin
- ✅ Password validation working

**Testing**:
- [ ] Test user registration (first user = admin)
- [ ] Test user registration (subsequent users = player)
- [ ] Test login with valid credentials
- [ ] Test login with invalid credentials
- [ ] Test token generation
- [ ] Test token verification
- [ ] Test password hashing and verification
- [ ] Test password strength validation
- [ ] Test duplicate username/email prevention

---

## Phase 3: Token Management

### 3.1 Refresh Token Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/refresh` in `app/routes/auth_routes.py`
  - Validate refresh token
  - Check refresh token expiration
  - Verify refresh token in database
  - Generate new access token
  - Optionally rotate refresh token
  - Update refresh token last_used_at
  - Return new tokens
  - Handle errors (invalid token, expired)

**Response**:
```json
{
  "token": "new-jwt-access-token",
  "refresh_token": "new-refresh-token" | null,
  "expires_in": 3600
}
```

### 3.2 Logout Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/logout` in `app/routes/auth_routes.py`
  - Extract token from Authorization header
  - Verify token
  - Get token ID (jti claim)
  - Add token to blacklist
  - Optionally invalidate refresh token
  - Return success message
  - Handle errors (invalid token, already logged out)

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

### 3.3 Revoke Token Endpoint
**Tasks**:
- [ ] Implement `POST /api/auth/revoke` in `app/routes/auth_routes.py`
  - Extract token from Authorization header
  - Verify token and get user
  - Check permissions (self or admin)
  - If token_id provided: revoke specific token
  - If no token_id: revoke all user tokens (admin only)
  - Add tokens to blacklist
  - Return success message
  - Handle errors (invalid token, insufficient permissions)

**Request Body** (optional):
```json
{
  "token_id": "jwt-jti-claim"
}
```

**Response**:
```json
{
  "message": "Token revoked successfully",
  "revoked_count": 1
}
```

### 3.4 Token Blacklist Service
**Tasks**:
- [ ] Enhance `app/services/token_service.py` with blacklist management
  - `cleanup_expired_tokens()` - Remove expired tokens from blacklist
  - `is_token_blacklisted(token_id: str) -> bool` - Check if token is blacklisted
  - `blacklist_token(token_id: str, user_id: UUID, expires_at: datetime)` - Add token to blacklist
  - `revoke_all_user_tokens(user_id: UUID)` - Revoke all tokens for a user

### 3.5 Refresh Token Storage
**Tasks**:
- [ ] Update `RefreshToken` model if needed
- [ ] Implement refresh token storage in database
- [ ] Implement refresh token lookup
- [ ] Implement refresh token rotation (optional)
- [ ] Implement refresh token cleanup (expired tokens)

**Deliverables**:
- ✅ Token refresh working
- ✅ Logout working
- ✅ Token revocation working
- ✅ Token blacklist working
- ✅ Refresh token storage working

**Testing**:
- [ ] Test token refresh with valid refresh token
- [ ] Test token refresh with expired refresh token
- [ ] Test token refresh with invalid refresh token
- [ ] Test logout (token blacklisted)
- [ ] Test token revocation (single token)
- [ ] Test token revocation (all user tokens - admin)
- [ ] Test token blacklist check
- [ ] Test expired token cleanup

---

## Phase 4: User Management

### 4.1 User Profile Endpoints
**Tasks**:
- [ ] Implement `GET /api/users/{user_id}` in `app/routes/user_routes.py`
  - Verify authentication
  - Check permissions (self or admin)
  - Get user from database
  - Return user profile (without password_hash)
  - Handle errors (user not found, insufficient permissions)

- [ ] Implement `PUT /api/users/{user_id}` in `app/routes/user_routes.py`
  - Verify authentication
  - Check permissions (self or admin)
  - Validate input (email, password optional)
  - Update user profile
  - If password provided: validate, hash, save to history
  - Return updated user profile
  - Handle errors (validation errors, duplicate email)

- [ ] Implement `GET /api/users/username/{username}` in `app/routes/user_routes.py`
  - Public endpoint (no auth required)
  - Get user by username
  - Return user profile (limited fields)
  - Handle errors (user not found)

### 4.2 Role Management Endpoints
**Tasks**:
- [ ] Implement `PUT /api/users/{user_id}/role` in `app/routes/user_routes.py`
  - Verify authentication
  - Check admin permission
  - Validate role (viewer, player, writer, admin)
  - Prevent demoting first user
  - Prevent modifying system users (unless admin)
  - Update user role
  - Log role change (future: audit log)
  - Return updated user
  - Handle errors (insufficient permissions, invalid role)

- [ ] Implement `GET /api/users` in `app/routes/user_routes.py`
  - Verify authentication
  - Check admin permission
  - Support query parameters: role, limit, offset
  - Return paginated user list
  - Handle errors (insufficient permissions)

### 4.3 System User Endpoint
**Tasks**:
- [ ] Implement `POST /api/users/system` in `app/routes/user_routes.py`
  - Verify service token (not user JWT)
  - Validate input (username, email, role)
  - Create system user (is_system_user = True)
  - Return user profile
  - Handle errors (invalid service token, duplicate username/email)

**Request Body**:
```json
{
  "username": "admin",
  "email": "admin@system",
  "role": "admin"
}
```

### 4.4 Permission Middleware
**Tasks**:
- [ ] Create `app/middleware/auth.py`
  - `require_auth(f)` - Decorator to require authentication
  - `require_role(role: str)` - Decorator to require specific role
  - `require_admin(f)` - Decorator to require admin role
  - `get_current_user()` - Get current user from token
  - `get_user_from_token(token: str) -> User | None` - Extract user from token

**Deliverables**:
- ✅ User profile endpoints working
- ✅ Role management working
- ✅ System user creation working
- ✅ Permission middleware working

**Testing**:
- [ ] Test get user profile (self)
- [ ] Test get user profile (admin viewing other)
- [ ] Test update user profile (self)
- [ ] Test update user profile (admin updating other)
- [ ] Test get user by username (public)
- [ ] Test update user role (admin)
- [ ] Test update user role (non-admin - should fail)
- [ ] Test list users (admin)
- [ ] Test create system user (with service token)
- [ ] Test permission middleware decorators

---

## Phase 5: Security & Rate Limiting

### 5.1 Rate Limiting
**Tasks**:
- [ ] Install Flask-Limiter or implement custom rate limiting
- [ ] Create `app/middleware/rate_limit.py`
  - Rate limit login: 5 attempts per 15 minutes per IP
  - Rate limit registration: 3 registrations per hour per IP
  - Rate limit token refresh: 10 requests per hour per user
  - Rate limit password reset: 3 requests per hour per email (future)
- [ ] Apply rate limiting to endpoints
- [ ] Return rate limit headers in responses

**Rate Limit Headers**:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1234567890
```

### 5.2 Password History
**Tasks**:
- [ ] Enhance password service to check history
- [ ] Save password to history on password change
- [ ] Check last 3 passwords on password change
- [ ] Implement password history cleanup (optional: old entries)

### 5.3 Token Blacklist Cleanup
**Tasks**:
- [ ] Create background task or scheduled job
- [ ] Clean up expired tokens from blacklist
- [ ] Run cleanup periodically (e.g., daily)
- [ ] Log cleanup statistics

### 5.4 Email Verification (Placeholder)
**Tasks**:
- [ ] Add email verification token generation
- [ ] Add email verification endpoint (placeholder)
- [ ] Mark email as verified for first user
- [ ] Require email verification for non-first users (can be bypassed for MVP)
- [ ] Store email verification token in user model

**Note**: Full email service integration is future enhancement. For MVP, this can be a placeholder that always succeeds.

### 5.5 Security Headers
**Tasks**:
- [ ] Add security headers to responses
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security` (for HTTPS in production)

### 5.6 Input Sanitization
**Tasks**:
- [ ] Sanitize all user inputs
- [ ] Validate and sanitize username
- [ ] Validate and sanitize email
- [ ] Prevent SQL injection (SQLAlchemy handles this)
- [ ] Prevent XSS in user data

**Deliverables**:
- ✅ Rate limiting working
- ✅ Password history working
- ✅ Token blacklist cleanup working
- ✅ Email verification placeholder working
- ✅ Security headers added
- ✅ Input sanitization working

**Testing**:
- [ ] Test rate limiting on login
- [ ] Test rate limiting on registration
- [ ] Test rate limiting on token refresh
- [ ] Test password history check
- [ ] Test token blacklist cleanup
- [ ] Test email verification flow (placeholder)
- [ ] Test security headers
- [ ] Test input sanitization

---

## Phase 6: Shared Auth Library

### 6.1 Token Validation Utilities
**Tasks**:
- [ ] Create `shared/auth/tokens/__init__.py`
- [ ] Create `shared/auth/tokens/validation.py`
  - `validate_jwt_token(token: str, secret: str) -> dict | None` - Validate JWT token
  - `decode_token(token: str, secret: str) -> dict | None` - Decode token without validation
  - `is_token_expired(token_payload: dict) -> bool` - Check expiration
  - `get_token_user_id(token_payload: dict) -> UUID | None` - Extract user ID
  - `get_token_role(token_payload: dict) -> str | None` - Extract role

### 6.2 Permission Checking Utilities
**Tasks**:
- [ ] Create `shared/auth/permissions/__init__.py`
- [ ] Create `shared/auth/permissions/rbac.py`
  - `has_role(user_role: str, required_role: str) -> bool` - Check if user has required role
  - `has_permission(user_role: str, permission: str) -> bool` - Check permission
  - `can_access_resource(user_role: str, resource_role: str) -> bool` - Check resource access
  - `ROLE_HIERARCHY` - Role hierarchy constant

**Role Hierarchy**:
```python
ROLE_HIERARCHY = {
    'viewer': 0,
    'player': 1,
    'writer': 2,
    'admin': 3
}
```

### 6.3 Service Token Utilities
**Tasks**:
- [ ] Create `shared/auth/tokens/service_tokens.py`
  - `validate_service_token(token: str, secret: str) -> dict | None` - Validate service token
  - `get_service_name(token_payload: dict) -> str | None` - Extract service name
  - `is_service_token(token_payload: dict) -> bool` - Check if token is service token

### 6.4 Documentation
**Tasks**:
- [ ] Update `shared/auth/tokens/README.md` with usage examples
- [ ] Update `shared/auth/permissions/README.md` with usage examples
- [ ] Add code examples for each utility function

**Deliverables**:
- ✅ Token validation utilities working
- ✅ Permission checking utilities working
- ✅ Service token utilities working
- ✅ Documentation complete

**Testing**:
- [ ] Test token validation utilities
- [ ] Test permission checking utilities
- [ ] Test service token utilities
- [ ] Test integration with Wiki Service

---

## Phase 7: Testing & Documentation

### 7.1 Unit Tests
**Tasks**:
- [ ] Test password service
  - Password hashing
  - Password verification
  - Password strength validation
  - Password history
- [ ] Test token service
  - Token generation
  - Token verification
  - Token blacklist
  - Service token generation
- [ ] Test auth service
  - User registration
  - User login
  - Token refresh
  - Logout
  - Token revocation
- [ ] Test validators
  - Username validation
  - Email validation
  - Password validation
- [ ] Test models
  - User model methods
  - Model relationships
  - Model serialization

### 7.2 Integration Tests
**Tasks**:
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test token refresh flow
- [ ] Test logout flow
- [ ] Test user profile endpoints
- [ ] Test role management endpoints
- [ ] Test permission middleware
- [ ] Test rate limiting

### 7.3 API Tests
**Tasks**:
- [ ] Test all endpoints with valid inputs
- [ ] Test all endpoints with invalid inputs
- [ ] Test error responses
- [ ] Test authentication requirements
- [ ] Test permission requirements
- [ ] Test rate limiting

### 7.4 Documentation
**Tasks**:
- [ ] Update `services/auth/README.md` with:
  - Setup instructions
  - Configuration guide
  - API endpoint summary
  - Testing instructions
- [ ] Create API usage examples
- [ ] Document environment variables
- [ ] Document database schema
- [ ] Document security considerations

### 7.5 CI/CD Integration
**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Set up test database (`arcadium_testing_auth`)
- [ ] Configure test environment
- [ ] Add test coverage reporting
- [ ] Add linting/formatting checks

**Deliverables**:
- ✅ Comprehensive test coverage
- ✅ All tests passing
- ✅ Documentation complete
- ✅ CI/CD configured

**Testing Goals**:
- 80%+ code coverage
- All endpoints tested
- All error cases tested
- All security features tested

---

## Implementation Checklist

### Phase 1: Foundation ✅
- [ ] Project structure
- [ ] Database models
- [ ] Migrations
- [ ] Configuration

### Phase 2: Core Authentication ✅ COMPLETE
- [x] Password service
- [x] Token service
- [x] Auth service
- [x] Validators
- [x] Registration endpoint
- [x] Login endpoint
- [x] Verify token endpoint
- [x] UI Integration (SignInPage, AuthContext, Header auth)
- [x] Comprehensive test coverage (90+ client tests)

### Phase 3: Token Management
- [ ] Refresh token endpoint
- [ ] Logout endpoint
- [ ] Revoke token endpoint
- [ ] Token blacklist service
- [ ] Refresh token storage

### Phase 4: User Management
- [ ] User profile endpoints
- [ ] Role management endpoints
- [ ] System user endpoint
- [ ] Permission middleware

### Phase 5: Security
- [ ] Rate limiting
- [ ] Password history
- [ ] Token cleanup
- [ ] Email verification placeholder
- [ ] Security headers
- [ ] Input sanitization

### Phase 6: Shared Library
- [ ] Token validation utilities
- [ ] Permission checking utilities
- [ ] Service token utilities
- [ ] Documentation

### Phase 7: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] API tests
- [ ] Documentation
- [ ] CI/CD

---

## Dependencies

### Python Packages
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.9
python-dotenv==1.0.0
PyJWT==2.8.0
bcrypt==4.0.1
python-dateutil==2.8.2
Flask-Limiter==3.5.0  # For rate limiting
pytest==7.4.3
pytest-cov==4.1.0
```

### External Services
- PostgreSQL database
- (Future) Email service for verification

### Integration Points
- Wiki Service (for token validation)
- Frontend client (for login/registration UI)
- Other services (for service tokens)

---

## Testing Strategy

### Unit Tests
- Test each service independently
- Mock external dependencies
- Test edge cases
- Test error handling

### Integration Tests
- Test full flows (register → login → use token)
- Test database interactions
- Test token lifecycle

### API Tests
- Test all endpoints
- Test authentication
- Test authorization
- Test error responses
- Test rate limiting

### Security Tests
- Test password security
- Test token security
- Test rate limiting
- Test input validation
- Test SQL injection prevention

---

## Next Steps After Implementation

1. **Frontend Integration**
   - Create login/registration UI
   - Integrate with Auth Service API
   - Handle token storage
   - Handle token refresh

2. **Wiki Service Integration**
   - Update Wiki Service to use Auth Service
   - Implement token validation
   - Implement role checking
   - Update all protected endpoints

3. **Other Services Integration**
   - Generate service tokens
   - Integrate service token validation
   - Update service-to-service auth

4. **Future Enhancements**
   - Email verification (full implementation)
   - Password reset
   - Two-factor authentication
   - OAuth2 integration
   - Audit logging
   - Session management dashboard

---

## Notes

- Follow patterns from Wiki Service for consistency
- Use Flask blueprints for route organization
- Use SQLAlchemy models for database interaction
- Use Flask-Migrate for database migrations
- Use environment variables for configuration
- Use pytest for testing
- Use type hints where helpful
- Document all public functions
- Follow PEP 8 style guide

---

## Success Criteria

The Auth Service is complete when:

1. ✅ All endpoints implemented and working
2. ✅ All security features implemented
3. ✅ Comprehensive test coverage (80%+)
4. ✅ Documentation complete
5. ✅ CI/CD configured
6. ✅ Can register first user (admin)
7. ✅ Can register subsequent users (player)
8. ✅ Can login and get tokens
9. ✅ Can verify tokens
10. ✅ Can refresh tokens
11. ✅ Can logout and revoke tokens
12. ✅ Can manage user profiles
13. ✅ Can manage user roles (admin)
14. ✅ Rate limiting working
15. ✅ Password security working
16. ✅ Shared auth library working
17. ✅ Wiki Service can integrate
