# Service Dependencies and Integration

## Overview

This document outlines dependencies between services and how they integrate with each other.

## Service Dependency Graph

```
┌─────────────────┐
│  Auth Service   │ (Foundational - no dependencies)
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  Wiki Service   │  │ Notification Svc  │
└─────────────────┘  └──────────────────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Other Services │
         └─────────────────┘
```

## Wiki Service Dependencies

### Auth Service

**Purpose**: Authentication and authorization

**Integration Points**:
1. **JWT Token Validation**
   - All authenticated wiki endpoints validate JWT tokens
   - Uses `/api/auth/verify` endpoint or shared validation library
   - Token in `Authorization: Bearer <token>` header

2. **User Role Checking**
   - Wiki checks user roles for permission enforcement
   - Roles: viewer, player, writer, admin
   - Determines access to: view, comment, edit, delete, admin functions

3. **User Profile Lookup**
   - Display user information in comments and page metadata
   - Endpoints used:
     - `GET /api/users/{user_id}` - Get user by ID
     - `GET /api/users/username/{username}` - Get user by username

4. **Admin User for AI Content**
   - Wiki sync utility needs to find/create "admin" system user
   - AI-written pages assigned to admin user
   - Uses `GET /api/users/username/admin` to find admin user

**Shared Code**:
- `shared/auth/tokens/` - Token validation utilities
- `shared/auth/permissions/` - Permission checking helpers

### Notification Service

**Purpose**: Internal messaging for system notifications

**Integration Points**:
1. **Oversized Page Notifications**
   - When admin sets/lowers page size limit
   - Wiki Service sends notifications to page authors
   - Notification includes:
     - Subject: "Page Size Limit Exceeded"
     - Content: Details about page size and due date
     - Action URL: Link to affected page
     - Metadata: Page ID, sizes, due date

2. **Service Authentication**
   - Wiki Service uses service token (not user JWT)
   - Allows services to send notifications on behalf of system
   - Endpoint: `POST /api/notifications/send`

3. **Error Handling**
   - Notification failures are non-blocking
   - Wiki Service logs but doesn't fail if notification fails
   - Ensures wiki operations continue even if notifications fail

**Notification Format**:
```json
{
  "recipient_ids": ["author-uuid"],
  "subject": "Page Size Limit Exceeded",
  "content": "Your page '[Title]' exceeds...",
  "type": "warning",
  "action_url": "/wiki/pages/{slug}",
  "metadata": {
    "page_id": "uuid",
    "notification_type": "oversized_page"
  }
}
```

## Auth Service Dependencies

**No dependencies** - Foundational service used by all other services.

## Notification Service Dependencies

### Auth Service

**Purpose**: User lookup and authentication

**Integration Points**:
1. **User Lookup**
   - Validate recipient user IDs exist
   - Get user information for notifications
   - Endpoint: `GET /api/users/{user_id}`

2. **Service Authentication**
   - Validate service tokens for service-to-service calls
   - Separate from user JWT authentication

## Shared Code Dependencies

### shared/auth/

**Used By**: Auth Service, Wiki Service, and other services

**Contents**:
- Token generation utilities
- Token validation functions
- Permission checking helpers
- JWT handling

### shared/protocols/

**Used By**: All services

**Contents**:
- API schemas
- Message formats
- Data models

### shared/utils/

**Used By**: All services

**Contents**:
- Logging utilities
- Validation helpers
- Error handling
- Common utilities

## Integration Patterns

### Service-to-Service Communication

1. **HTTP REST APIs**
   - Services communicate via HTTP REST endpoints
   - JSON request/response format
   - Standard HTTP status codes

2. **Authentication**
   - **User requests**: JWT tokens from Auth Service
   - **Service requests**: Service tokens (separate from user JWT)
   - Tokens in `Authorization` header

3. **Error Handling**
   - Services handle errors gracefully
   - Non-critical operations (like notifications) don't block main operations
   - Proper error logging and monitoring

4. **Shared Libraries**
   - Common code in `shared/` directory
   - Services import shared utilities
   - Reduces code duplication
   - Ensures consistency

## Database Sharing

### Shared Database (PostgreSQL)

All services use the same PostgreSQL database with separate schemas:
- `wiki` schema for Wiki Service
- `auth` schema for Auth Service
- `notification` schema for Notification Service

**Benefits**:
- Single database connection pool
- Easier cross-service queries (if needed)
- Simplified backup and maintenance
- Schema-level isolation

**Connection Configuration:**
- Connection string in environment variables
- Connection pooling: 10 connections per service (configurable)
- Max connections: 100 total (PostgreSQL default)
- Connection timeout: 5 seconds

**Migration Strategy:**
- Each service manages its own schema migrations
- Migrations run on service startup
- Version tracking per schema

## API Gateway Pattern (Future)

For production, consider an API Gateway that:
- Routes requests to appropriate services
- Handles authentication centrally
- Provides unified API documentation
- Rate limiting and throttling

## Service Discovery

### Current Approach
- **Environment Variables**: Service URLs stored in environment variables
- **Docker Compose**: Services use Docker service names for local development
- **Configuration**: Each service has config file with service URLs
- Example: `AUTH_SERVICE_URL=http://auth:8000` (Docker) or `http://localhost:8000` (local)

### Service URLs
- Auth Service: `http://auth:8000` (Docker) / `http://localhost:8000` (local)
- Notification Service: `http://notification:8006` (Docker) / `http://localhost:8006` (local)
- Wiki Service: `http://wiki:5000` (Docker) / `http://localhost:5000` (local)

### Health Checks

All services implement health check endpoints:
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "auth",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Health Check Status:**
- `healthy`: Service is operational
- `degraded`: Service is running but some features unavailable
- `unhealthy`: Service is not operational

**Used For:**
- Docker Compose health checks
- Service status monitoring
- Load balancer health checks (future)

## Error Handling and Retries

### Retry Logic
- **Retry Attempts**: 3 attempts for failed service calls
- **Backoff Strategy**: Exponential backoff (1s, 2s, 4s)
- **Timeout**: 5 seconds per request
- **Circuit Breaker**: Not implemented (future enhancement)

### Error Handling
- Services handle errors gracefully
- Non-critical operations (like notifications) don't block main operations
- Proper error logging and monitoring
- Failed requests logged with context

## Service Discovery (Future)

For microservices at scale:
- Service registry
- Service mesh (Istio, Linkerd)
- Load balancing
- Service health monitoring dashboard

## Current Architecture

### Simple Direct Communication

```
Client → Wiki Service → Auth Service (for validation)
Client → Wiki Service → Notification Service (for notifications)
Client → Auth Service (for login/registration)
```

### Benefits of Current Approach

- Simple and straightforward
- Easy to understand and debug
- No additional infrastructure needed
- Good for development and small-scale deployment

## Summary

### Wiki Service Needs

1. **Auth Service** for:
   - JWT token validation
   - User role checking
   - User profile lookup
   - Admin user for AI content

2. **Notification Service** for:
   - Sending oversized page notifications
   - Internal messaging to users

### Documentation Created

- [Auth Service Specification](auth-service.md)
- [Auth Service API](api/auth-api.md)
- [Notification Service Specification](notification-service.md)
- [Notification Service API](api/notification-api.md)

All services now have basic documentation with wiki-specific integration details included.
