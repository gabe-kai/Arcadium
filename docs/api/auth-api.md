# Auth Service API Documentation

## Overview

The Auth Service provides authentication and authorization for all Arcadium services, including user management, JWT token generation and validation, and role-based access control.

## Base URL
```
http://localhost:8000/api
```

## Authentication

Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### User Registration

#### Register New User
```
POST /api/auth/register
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Note:** 
- First user to register automatically receives `admin` role
- Subsequent users default to `player` role
- Email verification required for non-first users
- Password must meet requirements (8+ chars, uppercase, lowercase, number)

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "newuser",
    "email": "user@example.com",
    "role": "player",  // or "admin" if first user
    "is_first_user": false,  // true for first user
    "email_verified": false,  // true for first user
    "created_at": "2024-01-01T00:00:00Z"
  },
  "token": "jwt-token-here",
  "requires_email_verification": true  // false for first user
}
```

**Permissions:** Public

**Rate Limit:** 3 registrations per hour per IP

---

### Authentication

#### Login
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "username",
  "password": "password"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "username",
    "email": "user@example.com",
    "role": "player"
  },
  "token": "jwt-token-here",
  "expires_in": 3600
}
```

**Permissions:** Public

---

#### Verify Token
```
POST /api/auth/verify
```

**Request Body:**
```json
{
  "token": "jwt-token-here"
}
```

**Response:**
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

**Permissions:** Public (for token validation)

---

#### Logout
```
POST /api/auth/logout
```

**Request Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

**Note:** Token is added to blacklist. User should be redirected to home page as viewer.

**Permissions:** Authenticated users

---

#### Refresh Token
```
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "token": "refresh-token-here"
}
```

**Response:**
```json
{
  "token": "new-jwt-token-here",
  "expires_in": 3600
}
```

**Permissions:** Public (with valid refresh token)

**Rate Limit:** 10 requests per hour per user

---

#### Revoke Token
```
POST /api/auth/revoke
```

**Request Body:**
```json
{
  "token_id": "jwt-jti-claim"  // Optional: specific token, or omit to revoke all user tokens
}
```

**Response:**
```json
{
  "message": "Token revoked successfully",
  "revoked_count": 1
}
```

**Permissions:** Self (own tokens) or Admin (any user's tokens)

---

### User Management

#### Get User Profile
```
GET /api/users/{user_id}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "username",
  "email": "user@example.com",
  "role": "player",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Self or Admin

---

#### Update User Profile
```
PUT /api/users/{user_id}
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "password": "newpassword"  // Optional
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "username",
  "email": "newemail@example.com",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Self or Admin

---

#### Get User by Username
```
GET /api/users/username/{username}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "username",
  "email": "user@example.com",
  "role": "player"
}
```

**Permissions:** Public (for username lookup)

---

### Role Management (Admin Only)

#### Update User Role
```
PUT /api/users/{user_id}/role
```

**Request Body:**
```json
{
  "role": "writer"  // "viewer", "player", "writer", or "admin"
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "username",
  "role": "writer",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Admin

---

#### List Users
```
GET /api/users
```

**Query Parameters:**
- `role` (optional): Filter by role
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "username",
      "email": "user@example.com",
      "role": "player"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

**Permissions:** Admin

---

## User Roles

### Role Definitions

- **viewer**: Unregistered users, can view public content
- **player**: Registered users, can view and comment
- **writer**: Can create and edit content
- **admin**: Full access, can manage users and system settings

### Role Hierarchy

```
admin > writer > player > viewer
```

## JWT Token Structure

### Token Payload (User JWT)
```json
{
  "user_id": "uuid",
  "username": "username",
  "role": "player",
  "jti": "token-id",  // JWT ID for revocation
  "iat": 1234567890,
  "exp": 1234571490  // 1 hour from issue
}
```

### Service Token Payload
```json
{
  "service_id": "uuid",
  "service_name": "wiki",
  "type": "service",
  "jti": "service-token-id",
  "iat": 1234567890,
  "exp": 1234601490  // 90 days from issue
}
```

### Token Validation

Services should validate tokens by:
1. Calling `/api/auth/verify` endpoint, OR
2. Using shared JWT validation library from `shared/auth/`

## Integration with Wiki Service

### Wiki Service Requirements

The Wiki Service requires the Auth Service to:

1. **Validate JWT Tokens**
   - All authenticated endpoints need token validation
   - Use `/api/auth/verify` or shared validation library

2. **User Role Information**
   - Wiki needs to check user roles for permission checks
   - Roles: viewer, player, writer, admin

3. **User Profile Lookup**
   - Display user information (username, etc.) in comments, page metadata
   - Use `/api/users/{user_id}` or `/api/users/username/{username}`

4. **Admin User Creation**
   - First registered user automatically becomes admin
   - Wiki sync utility can use `/api/users/username/{username}` to find admin user
   - Or use `POST /api/users/system` with service token to create system user

### Shared Authentication

Both services use shared authentication utilities from `shared/auth/`:
- Token generation
- Token validation
- Permission checking

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": {
    "field": "error message"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

