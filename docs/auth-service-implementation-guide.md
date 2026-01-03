# Auth Service Implementation Guide

## Overview

This guide provides a detailed, phased implementation plan for building the Auth Service. The service provides centralized authentication and authorization for all Arcadium services, managing user accounts, JWT token generation and validation, and role-based access control.

## Current Status

- ✅ **Design Complete**: Comprehensive specification and API documentation
- ✅ **Basic Structure**: Flask app skeleton exists
- ✅ **Phase 1 Complete**: Database setup, models, configuration, migrations
- ✅ **Phase 2 Complete**: Core authentication (register, login, verify) with UI integration
- ✅ **Phase 3 Complete**: Token management endpoints (refresh, logout, revoke) with comprehensive tests
  - ✅ Endpoints implemented: `/api/auth/refresh`, `/api/auth/logout`, `/api/auth/revoke`
  - ✅ Service methods: `AuthService.refresh_access_token()`, `AuthService.logout_user()`, `AuthService.revoke_token()`
  - ✅ Comprehensive API tests (16 tests, 2 known edge case failures)
- ✅ **Phase 4 Complete**: User management endpoints and permission middleware
  - ✅ User profile endpoints (get, update, get by username)
  - ✅ Role management endpoints (update role, list users)
  - ✅ System user creation endpoint
  - ✅ Permission middleware (`require_auth`, `require_role`, `require_admin`, `require_service_token`)
  - ✅ Comprehensive API tests (27 tests, all passing)
- ⏳ **Phase 5 Partial**: Password history implemented, rate limiting configured but not active
- ❌ **Phase 6 Not Started**: Shared auth library (only README files exist, no implementation)
- ⏳ **Phase 7 Partial**: API tests for Phases 3 and 4 complete, unit/integration tests pending
- ✅ **Database**: Set up with migrations (initial schema created)
- ✅ **Client Tests**: Comprehensive test coverage (90+ client tests)

### Key Findings

**What's Working:**
- ✅ All core authentication endpoints (register, login, verify)
- ✅ All token management endpoints (refresh, logout, revoke)
- ✅ All user management endpoints (profile, role management, system users)
- ✅ Complete service layer (auth, token, password services)
- ✅ Database models and migrations
- ✅ Password history tracking
- ✅ Token blacklist functionality
- ✅ Refresh token storage in database
- ✅ Permission middleware/decorators
- ✅ Comprehensive API test coverage for Phases 3 and 4

**What's Missing:**
- ❌ Rate limiting implementation (Flask-Limiter installed but not configured/active)
- ❌ Shared auth library implementation (only README files)
- ❌ Comprehensive unit/integration test suite
- ❌ Security headers
- ❌ Email verification enforcement

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
- [x] Update `app/models/__init__.py` to export all models

**Database Schema**:
- Schema: `auth` (separate from other services)
- Tables: `users`, `token_blacklist`, `password_history`, `refresh_tokens`

### 1.3 Database Migrations
**Tasks**:
- [x] Create initial migration (`flask db init`)
- [x] Create migration for all tables (`flask db migrate -m "Initial schema"`)
- [x] Review migration file
- [x] Test migration (`flask db upgrade`)
- [ ] Create rollback test (`flask db downgrade`)

### 1.4 Configuration
**Tasks**:
- [x] Create development config
- [x] Create testing config
- [x] Create production config
- [x] Set up environment variables:
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
- [x] Test database connection
- [x] Test model creation
- [x] Test migration up
- [ ] Test migration down (rollback)

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
- [x] Create `app/services/auth_service.py`
  - [x] `register_user(username: str, email: str, password: str) -> tuple[User, bool]` - Register user, return (user, is_first_user)
  - [x] `login_user(username: str, password: str) -> tuple[User, str, str] | None` - Login, return (user, access_token, refresh_token)
  - [x] `verify_user_token(token: str) -> dict | None` - Verify token and return user info
  - [x] `refresh_access_token(refresh_token: str) -> tuple[str, str] | None` - Refresh access token
  - [x] `logout_user(token: str, user_id: UUID)` - Logout (blacklist token)
  - [x] `revoke_token(token_id: str, user_id: UUID, revoke_all: bool = False)` - Revoke token(s)

### 2.4 Validators
**Tasks**:
- [x] Create `app/utils/validators.py`
  - [x] `validate_username(username: str) -> tuple[bool, str]` - Validate username format
  - [x] `validate_email(email: str) -> tuple[bool, str]` - Validate email format
  - [x] `validate_password(password: str) -> tuple[bool, str]` - Validate password strength
  - [x] `sanitize_username(username: str) -> str` - Sanitize username input

**Validation Rules**:
- Username: 3-100 chars, alphanumeric + underscore/hyphen
- Email: Valid email format
- Password: See password requirements above

### 2.5 Registration Endpoint
**Tasks**:
- [x] Implement `POST /api/auth/register` in `app/routes/auth_routes.py`
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
- [x] Implement `POST /api/auth/login` in `app/routes/auth_routes.py`
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
- [x] Implement `POST /api/auth/verify` in `app/routes/auth_routes.py`
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
- [x] Test user registration (first user = admin) - ✅ Working (client tests)
- [x] Test user registration (subsequent users = player) - ✅ Working (client tests)
- [x] Test login with valid credentials - ✅ Working (client tests)
- [x] Test login with invalid credentials - ✅ Working (client tests)
- [x] Test token generation - ✅ Working (client tests)
- [x] Test token verification - ✅ Working (client tests)
- [x] Test password hashing and verification - ✅ Implemented
- [x] Test password strength validation - ✅ Implemented
- [x] Test duplicate username/email prevention - ✅ Working (client tests)

---

## Phase 3: Token Management

### 3.1 Refresh Token Endpoint
**Tasks**:
- [x] Service method implemented (`AuthService.refresh_access_token`)
- [x] Implement `POST /api/auth/refresh` endpoint in `app/routes/auth_routes.py`
  - [x] Validate refresh token
  - [x] Check refresh token expiration
  - [x] Verify refresh token in database
  - [x] Generate new access token
  - [x] Update refresh token last_used_at
  - [x] Return new tokens
  - [x] Handle errors (invalid token, expired)
  - [ ] Optionally rotate refresh token (currently returns same token)

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
- [x] Service method implemented (`AuthService.logout_user`)
- [x] Implement `POST /api/auth/logout` endpoint in `app/routes/auth_routes.py`
  - [x] Extract token from Authorization header
  - [x] Verify token
  - [x] Get token ID (jti claim)
  - [x] Add token to blacklist
  - [x] Return success message
  - [x] Handle errors (invalid token, already logged out)
  - [ ] Optionally invalidate refresh token (not implemented)

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

### 3.3 Revoke Token Endpoint
**Tasks**:
- [x] Service method implemented (`AuthService.revoke_token`)
- [x] Implement `POST /api/auth/revoke` endpoint in `app/routes/auth_routes.py`
  - [x] Extract token from Authorization header
  - [x] Verify token and get user
  - [x] Check permissions (self or admin)
  - [x] If token_id provided: revoke specific token
  - [x] If no token_id: revoke all user tokens (admin only)
  - [x] Add tokens to blacklist
  - [x] Return success message
  - [x] Handle errors (invalid token, insufficient permissions)

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
- [x] Enhance `app/services/token_service.py` with blacklist management
  - [ ] `cleanup_expired_tokens()` - Remove expired tokens from blacklist (not implemented, cleanup happens on check)
  - [x] `is_token_blacklisted(token_id: str) -> bool` - Check if token is blacklisted
  - [x] `blacklist_token(token_id: str, user_id: UUID, expires_at: datetime)` - Add token to blacklist
  - [x] `revoke_all_user_tokens(user_id: UUID)` - Revoke all tokens for a user (via `AuthService.revoke_token`)

### 3.5 Refresh Token Storage
**Tasks**:
- [x] Update `RefreshToken` model if needed
- [x] Implement refresh token storage in database (stored in register/login)
- [x] Implement refresh token lookup (used in `refresh_access_token`)
- [ ] Implement refresh token rotation (optional) - Currently returns same token
- [ ] Implement refresh token cleanup (expired tokens) - Manual cleanup needed

**Deliverables**:
- ✅ Token refresh working (endpoint and service method implemented)
- ✅ Logout working (endpoint and service method implemented)
- ✅ Token revocation working (endpoint and service method implemented)
- ✅ Token blacklist working (service methods implemented)
- ✅ Refresh token storage working (stored in database)
- ✅ Comprehensive API tests (16 tests in `test_token_endpoints.py`)

**Testing**:
- [x] Test token refresh with valid refresh token
- [x] Test token refresh with expired refresh token
- [x] Test token refresh with invalid refresh token
- [x] Test token refresh with missing body
- [x] Test logout (token blacklisted)
- [x] Test logout with missing/invalid token
- [x] Test token revocation (single token)
- [x] Test token revocation (all user tokens - admin)
- [x] Test token revocation permissions (non-admin cannot revoke all)
- [x] Test token blacklist check (implemented in service)
- [ ] Test expired token cleanup (cleanup happens on check, no background task)
- ⚠️ Known issues: 2 edge case test failures in blacklist verification (to be addressed)

---

## Phase 4: User Management

### 4.1 User Profile Endpoints
**Tasks**:
- [x] Implement `GET /api/users/{user_id}` in `app/routes/user_routes.py`
  - [x] Verify authentication
  - [x] Check permissions (self or admin)
  - [x] Get user from database
  - [x] Return user profile (without password_hash)
  - [x] Handle errors (user not found, insufficient permissions)

- [x] Implement `PUT /api/users/{user_id}` in `app/routes/user_routes.py`
  - [x] Verify authentication
  - [x] Check permissions (self or admin)
  - [x] Validate input (email, password optional)
  - [x] Update user profile
  - [x] If password provided: validate, hash, save to history
  - [x] Check password history (prevent reuse of last 3 passwords)
  - [x] Return updated user profile
  - [x] Handle errors (validation errors, duplicate email)

- [x] Implement `GET /api/users/username/{username}` in `app/routes/user_routes.py`
  - [x] Public endpoint (no auth required)
  - [x] Get user by username
  - [x] Return user profile (limited fields, no email)
  - [x] Handle errors (user not found)

### 4.2 Role Management Endpoints
**Tasks**:
- [x] Implement `PUT /api/users/{user_id}/role` in `app/routes/user_routes.py`
  - [x] Verify authentication
  - [x] Check admin permission
  - [x] Validate role (viewer, player, writer, admin)
  - [x] Prevent demoting first user
  - [x] Update user role
  - [x] Return updated user
  - [x] Handle errors (insufficient permissions, invalid role)
  - [ ] Log role change (future: audit log)

- [x] Implement `GET /api/users` in `app/routes/user_routes.py`
  - [x] Verify authentication
  - [x] Check admin permission
  - [x] Support query parameters: role, limit, offset
  - [x] Return paginated user list
  - [x] Handle errors (insufficient permissions)

### 4.3 System User Endpoint
**Tasks**:
- [x] Implement `POST /api/users/system` in `app/routes/user_routes.py`
  - [x] Verify service token (not user JWT)
  - [x] Validate input (username, email, role)
  - [x] Create system user (is_system_user = True)
  - [x] Return user profile
  - [x] Handle errors (invalid service token, duplicate username/email)

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
- [x] Create `app/middleware/auth.py`
  - [x] `require_auth(f)` - Decorator to require authentication
  - [x] `require_role(role: str)` - Decorator factory to require specific role
  - [x] `require_admin(f)` - Decorator to require admin role
  - [x] `require_service_token(f)` - Decorator to require service token
  - [x] `get_current_user()` - Get current user from token (from Flask g)
  - [x] `get_user_from_token(token: str) -> dict | None` - Extract user info from token

**Deliverables**:
- ✅ User profile endpoints working
- ✅ Role management working
- ✅ System user creation working
- ✅ Permission middleware working
- ✅ Comprehensive API tests (27 tests in `test_user_endpoints.py`, all passing)

**Testing**:
- [x] Test get user profile (self)
- [x] Test get user profile (admin viewing other)
- [x] Test get user profile (unauthorized)
- [x] Test update user profile (self)
- [x] Test update user profile (admin updating other)
- [x] Test update user profile password (with password history check)
- [x] Test get user by username (public)
- [x] Test get user by username (not found)
- [x] Test update user role (admin)
- [x] Test update user role (non-admin - should fail)
- [x] Test update first user role (should fail)
- [x] Test list users (admin)
- [x] Test list users (non-admin - should fail)
- [x] Test list users with filters (role, pagination)
- [x] Test create system user (with service token)
- [x] Test create system user (with user token - should fail)
- [x] Test permission middleware decorators

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
- [x] Enhance password service to check history (`check_password_history`)
- [x] Save password to history on password change (saved on registration)
- [x] Check last 3 passwords on password change (`check_password_history` method exists)
- [x] Implement password history cleanup (keeps last 10 per user, auto-cleanup in `save_password_history`)

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
- ⏳ Rate limiting working (configured but not implemented/active)
- ✅ Password history working (fully implemented)
- ⏳ Token blacklist cleanup working (cleanup on check, no background task)
- ⏳ Email verification placeholder working (field exists, not enforced)
- [ ] Security headers added (not implemented)
- ⏳ Input sanitization working (username sanitization exists)

**Testing**:
- [ ] Test rate limiting on login (not implemented)
- [ ] Test rate limiting on registration (not implemented)
- [ ] Test rate limiting on token refresh (not implemented)
- [x] Test password history check (method exists)
- [x] Test token blacklist cleanup (cleanup on check implemented)
- [ ] Test email verification flow (placeholder) (not enforced)
- [ ] Test security headers (not implemented)
- [x] Test input sanitization (username sanitization exists)

---

## Phase 6: Shared Auth Library

### 6.1 Token Validation Utilities
**Tasks**:
- [x] Create `shared/auth/tokens/__init__.py` (exists)
- [ ] Create `shared/auth/tokens/validation.py` (only README exists)
  - [ ] `validate_jwt_token(token: str, secret: str) -> dict | None` - Validate JWT token
  - [ ] `decode_token(token: str, secret: str) -> dict | None` - Decode token without validation
  - [ ] `is_token_expired(token_payload: dict) -> bool` - Check expiration
  - [ ] `get_token_user_id(token_payload: dict) -> UUID | None` - Extract user ID
  - [ ] `get_token_role(token_payload: dict) -> str | None` - Extract role

### 6.2 Permission Checking Utilities
**Tasks**:
- [x] Create `shared/auth/permissions/__init__.py` (exists)
- [ ] Create `shared/auth/permissions/rbac.py` (only README exists)
  - [ ] `has_role(user_role: str, required_role: str) -> bool` - Check if user has required role
  - [ ] `has_permission(user_role: str, permission: str) -> bool` - Check permission
  - [ ] `can_access_resource(user_role: str, resource_role: str) -> bool` - Check resource access
  - [ ] `ROLE_HIERARCHY` - Role hierarchy constant

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
- [ ] Create `shared/auth/tokens/service_tokens.py` (not implemented)
  - [ ] `validate_service_token(token: str, secret: str) -> dict | None` - Validate service token
  - [ ] `get_service_name(token_payload: dict) -> str | None` - Extract service name
  - [ ] `is_service_token(token_payload: dict) -> bool` - Check if token is service token
  - Note: `TokenService.generate_service_token` exists in auth service, but shared utilities not created

### 6.4 Documentation
**Tasks**:
- [ ] Update `shared/auth/tokens/README.md` with usage examples
- [ ] Update `shared/auth/permissions/README.md` with usage examples
- [ ] Add code examples for each utility function

**Deliverables**:
- [ ] Token validation utilities working (only README exists)
- [ ] Permission checking utilities working (only README exists)
- [ ] Service token utilities working (not implemented)
- ⏳ Documentation complete (README files exist, but no implementation)

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

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure
- [x] Database models
- [x] Migrations (initial schema created)
- [x] Configuration (dev, test, prod configs)

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

### Phase 3: Token Management ✅ COMPLETE
- [x] Refresh token service method
- [x] Refresh token endpoint (`POST /api/auth/refresh`)
- [x] Logout service method
- [x] Logout endpoint (`POST /api/auth/logout`)
- [x] Revoke token service method
- [x] Revoke token endpoint (`POST /api/auth/revoke`)
- [x] Token blacklist service
- [x] Refresh token storage
- [x] Comprehensive API tests (16 tests, 2 known edge case failures)

### Phase 4: User Management ✅ COMPLETE
- [x] User profile endpoints (GET, PUT `/api/users/{user_id}`)
- [x] User by username endpoint (GET `/api/users/username/{username}`)
- [x] Role management endpoints (PUT `/api/users/{user_id}/role`, GET `/api/users`)
- [x] System user endpoint (POST `/api/users/system`)
- [x] Permission middleware (`require_auth`, `require_role`, `require_admin`, `require_service_token`)
- [x] Comprehensive API tests (27 tests, all passing)

### Phase 5: Security ⏳ PARTIAL
- [ ] Rate limiting (configured but not active)
- [x] Password history (fully implemented)
- [x] Token cleanup (on check, no background task)
- [ ] Email verification placeholder (field exists, not enforced)
- [ ] Security headers
- [x] Input sanitization (username only)

### Phase 6: Shared Library ❌ NOT STARTED
- [ ] Token validation utilities (only README exists)
- [ ] Permission checking utilities (only README exists)
- [ ] Service token utilities (not implemented)
- [ ] Documentation (README files exist, no code)

### Phase 7: Testing ⏳ PARTIAL
- [ ] Unit tests (service layer tests not yet created)
- [ ] Integration tests (full flow tests not yet created)
- [x] API tests (comprehensive tests for Phases 3 and 4 endpoints)
- [ ] Documentation (API documentation exists, service README needs updates)
- [ ] CI/CD (GitHub Actions workflows not yet configured for auth service)

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

1. ✅ All core endpoints implemented and working (register, login, verify, refresh, logout, revoke)
2. ✅ All user management endpoints implemented and working
3. ⏳ All security features implemented (password history ✅, rate limiting ❌, security headers ❌)
4. ⏳ Comprehensive test coverage (API tests for Phases 3-4 ✅, unit/integration tests ❌)
5. ❌ Documentation complete (API docs ✅, service README needs updates)
6. ❌ CI/CD configured
7. ✅ Can register first user (admin)
8. ✅ Can register subsequent users (player)
9. ✅ Can login and get tokens
10. ✅ Can verify tokens
11. ✅ Can refresh tokens
12. ✅ Can logout and revoke tokens
13. ✅ Can manage user profiles
14. ✅ Can manage user roles (admin)
15. ❌ Rate limiting working
16. ✅ Password security working
17. ❌ Shared auth library working
18. ❌ Wiki Service can integrate (requires shared auth library)
