# Service Documentation

This directory contains specifications for all Arcadium services.

## Services

### Wiki Service
Comprehensive documentation and planning wiki. See [Wiki Service Documentation](../wiki-service-specification.md).

### Auth Service
Centralized authentication and authorization for all services. See [Auth Service Specification](auth-service.md).

### Notification Service
Internal messaging and notification system. See [Notification Service Specification](notification-service.md).

## Documentation

- [Service Dependencies](service-dependencies.md) - Cross-service dependencies and integration patterns
- [Service Architecture](service-architecture.md) - Service communication, health checks, and deployment

## Service Dependencies

### Wiki Service Dependencies
- **Auth Service**: User authentication, JWT validation, role checking
- **Notification Service**: Internal messaging for oversized page notifications

### Auth Service Dependencies
- None (foundational service)

### Notification Service Dependencies
- **Auth Service**: User lookup, authentication

## Integration Patterns

### Service-to-Service Communication
- HTTP REST APIs
- JWT tokens for user authentication
- Service tokens for service-to-service calls
- Shared code libraries in `shared/` directory

### Shared Code
- `shared/auth/` - Authentication utilities
- `shared/protocols/` - API schemas and message formats
- `shared/utils/` - Common utilities
