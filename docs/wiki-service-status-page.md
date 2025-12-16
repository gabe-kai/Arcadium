# Wiki Service Status Page

## Overview

The Service Status Page is a static wiki page that displays the health status of all Arcadium services. It provides a centralized view of system health with visual indicators (red/yellow/green) and explanatory notes for any issues.

## Purpose

- **Visibility**: Provide a single location to check the status of all services
- **Transparency**: Keep users informed about system health and any issues
- **Operational**: Help administrators quickly identify and communicate service issues
- **Documentation**: Maintain a record of service status and maintenance windows

## Page Structure

### Location
- **Slug**: `service-status` or `system/service-status`
- **Type**: System page (`is_system_page = true`)
- **Access**: Public (viewable by all users)
- **Editing**: Admin only (status updates)

### Content Structure

```markdown
# Arcadium Service Status

*Last Updated: 2024-01-01 12:00:00 UTC*

## Services

| Service | Status | Last Check | Response Time | Notes |
|---------|--------|------------|---------------|-------|
| Wiki Service | 🟢 Healthy | 2024-01-01 12:00:00 | 5ms | All systems operational |
| Auth Service | 🟢 Healthy | 2024-01-01 12:00:00 | 12ms | - |
| Notification Service | 🟡 Degraded | 2024-01-01 12:00:00 | 250ms | High latency, investigating |
| Game Server | 🔴 Unhealthy | 2024-01-01 12:00:00 | N/A | Service restarting |
| Web Client | 🟢 Healthy | 2024-01-01 12:00:00 | 8ms | - |
| Admin Service | 🟢 Healthy | 2024-01-01 12:00:00 | 6ms | - |
| Assets Service | 🟢 Healthy | 2024-01-01 12:00:00 | 10ms | - |
| Chat Service | 🟢 Healthy | 2024-01-01 12:00:00 | 7ms | - |
| Leaderboard Service | 🟢 Healthy | 2024-01-01 12:00:00 | 9ms | - |
| Presence Service | 🟢 Healthy | 2024-01-01 12:00:00 | 11ms | - |

## Status Notes

### Notification Service (🟡 Degraded)
- **Issue**: High response latency detected (>200ms)
- **Impact**: Notifications may be delayed by up to 5 seconds
- **ETA**: Expected resolution within 1 hour
- **Last Updated**: 2024-01-01 11:45:00 UTC
- **Updated By**: admin@example.com

### Game Server (🔴 Unhealthy)
- **Issue**: Service restarting after unexpected crash
- **Impact**: Game unavailable, players cannot connect
- **ETA**: Expected resolution within 15 minutes
- **Last Updated**: 2024-01-01 11:50:00 UTC
- **Updated By**: admin@example.com

---

*Status checks run automatically every 60 seconds. Manual updates can be made by administrators.*
```

## Status Indicators

### 🟢 Green (Healthy)
- Service is fully operational
- All health checks passing
- Response time within acceptable range
- No known issues

**Criteria:**
- Health endpoint returns `200 OK`
- Status is `"healthy"`
- Response time < 100ms (or service-specific threshold)
- Database connection active (if applicable)

### 🟡 Yellow (Degraded)
- Service is partially operational
- Some functionality may be limited
- Performance issues or warnings
- Non-critical errors

**Criteria:**
- Health endpoint returns `200 OK` but status is `"degraded"`
- Response time > 100ms but < 1000ms
- Warnings present in health check response
- Partial functionality available

### 🔴 Red (Unhealthy)
- Service is down or critically impaired
- Critical functionality unavailable
- Errors preventing normal operation
- Requires immediate attention

**Criteria:**
- Health endpoint returns non-200 status
- Status is `"unhealthy"`
- Response time > 1000ms or timeout
- Critical errors in health check response
- Service unreachable

## Services to Monitor

### Core Services
1. **Wiki Service** (self)
   - Health endpoint: `GET /health`
   - Database connection check
   - File system access check

2. **Auth Service**
   - Health endpoint: `GET /health`
   - Database connection check
   - Token validation check

3. **Notification Service**
   - Health endpoint: `GET /health`
   - Database connection check
   - Message queue check (if applicable)

### Game Services
4. **Game Server**
   - Health endpoint: `GET /health` (if available)
   - Connection check
   - Player capacity check

5. **Web Client**
   - CDN/static asset availability
   - API connectivity check

### Supporting Services
6. **Admin Service**
   - Health endpoint: `GET /health`
   - Database connection check

7. **Assets Service**
   - Health endpoint: `GET /health`
   - Storage availability check

8. **Chat Service**
   - Health endpoint: `GET /health`
   - WebSocket connection check (if applicable)

9. **Leaderboard Service**
   - Health endpoint: `GET /health`
   - Database connection check

10. **Presence Service**
    - Health endpoint: `GET /health`
    - Database connection check

## Implementation

### Service Health Checker

Create a service to check health of all services:

```python
# app/services/service_status_service.py

class ServiceStatusService:
    """Service for checking health of all Arcadium services"""
    
    SERVICES = {
        'wiki': {
            'name': 'Wiki Service',
            'url': os.getenv('WIKI_SERVICE_URL', 'http://localhost:5000'),
            'health_endpoint': '/health'
        },
        'auth': {
            'name': 'Auth Service',
            'url': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8000'),
            'health_endpoint': '/health'
        },
        # ... other services
    }
    
    def check_service_health(self, service_id: str) -> Dict:
        """Check health of a specific service"""
        # Implementation
        
    def check_all_services(self) -> Dict[str, Dict]:
        """Check health of all services"""
        # Implementation
        
    def determine_status(self, health_response: Dict) -> str:
        """Determine status (healthy/degraded/unhealthy) from health response"""
        # Implementation
```

### API Endpoints

#### Get Service Status
```
GET /api/admin/service-status
```

**Response:**
```json
{
  "services": {
    "wiki": {
      "name": "Wiki Service",
      "status": "healthy",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 5,
      "details": {
        "database": "connected",
        "version": "1.0.0"
      }
    },
    "auth": {
      "name": "Auth Service",
      "status": "healthy",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 12,
      "details": {
        "database": "connected",
        "version": "1.0.0"
      }
    },
    "notification": {
      "name": "Notification Service",
      "status": "degraded",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 250,
      "details": {
        "database": "connected",
        "version": "1.0.0",
        "warnings": ["High latency detected"]
      }
    }
  },
  "last_updated": "2024-01-01T12:00:00Z"
}
```

#### Update Service Status (Admin Only)
```
PUT /api/admin/service-status
```

**Request:**
```json
{
  "service": "notification",
  "status": "degraded",
  "notes": "High latency detected, investigating",
  "eta": "2024-01-01T13:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Status updated",
  "service": "notification",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Status Page Update

The status page can be updated in two ways:

1. **Automatic**: Scheduled task checks all services and updates the page
2. **Manual**: Admin updates status via API or directly edits the page

### Health Check Integration

Each service should implement a `/health` endpoint that returns:

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "service": "service-name",
  "version": "1.0.0",
  "database": "connected" | "disconnected",
  "dependencies": {
    "dependency_name": "healthy" | "degraded" | "unhealthy"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## User Interface

### Display Options

1. **Table View** (default)
   - Compact table with all services
   - Status indicators (colored circles or emoji)
   - Sortable columns
   - Filterable by status

2. **Card View** (optional)
   - Individual cards for each service
   - More detailed information per service
   - Better for mobile devices

3. **Timeline View** (optional)
   - Historical status changes
   - Incident timeline
   - Uptime statistics

### Auto-Refresh

- Optional: Auto-refresh page every 60 seconds
- Show "Last updated" timestamp
- Indicate when refresh is in progress

## Access Control

- **View**: Public (all users can view)
- **Edit**: Admin only
- **API Updates**: Admin only (requires authentication)

## Maintenance Windows

Admins can manually set status to yellow/red with notes for planned maintenance:

```markdown
### Auth Service (🟡 Degraded)
- **Issue**: Planned maintenance window
- **Impact**: Authentication may be unavailable
- **ETA**: 2024-01-01 14:00:00 UTC
- **Last Updated**: 2024-01-01 13:00:00 UTC
```

## Error Handling

- **Service Unreachable**: Mark as red, note "Service unreachable"
- **Timeout**: Mark as yellow/red based on timeout duration
- **Invalid Response**: Mark as yellow, note "Invalid health check response"
- **Partial Failure**: Mark as degraded if some checks pass but others fail

## Testing

### Unit Tests
- Service health check logic
- Status determination logic
- Response parsing

### Integration Tests
- Health endpoint calls
- Status page updates
- API endpoint authentication

### End-to-End Tests
- Full status check workflow
- Page rendering with various statuses
- Admin status updates

## Future Enhancements

- **Historical Data**: Track status over time
- **Alerting**: Notify admins when services go down
- **Metrics Dashboard**: Response time graphs, uptime percentages
- **Service Dependencies Graph**: Visual representation of service dependencies
- **Incident Management**: Link to incident reports
- **Scheduled Checks**: Configurable check intervals per service

## Related Documentation

- [Service Architecture](../services/service-architecture.md) - Service communication and health checks
- [Service Dependencies](../services/service-dependencies.md) - Service relationships
- [Wiki Admin Dashboard](wiki-admin-dashboard.md) - Admin features
