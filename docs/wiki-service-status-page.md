# Service Management Page

## Overview

The Service Management Page is an interactive web interface that provides real-time monitoring and management of all Arcadium services. It displays service health status, process information, resource usage, and recent logs in a user-friendly dashboard format.

## Purpose

- **Real-time Monitoring**: Live status updates every 15 seconds for all services
- **Visibility**: Centralized view of system health with visual indicators (🟢 healthy, 🟡 degraded, 🔴 unhealthy)
- **Operational**: Help administrators quickly identify issues and view service details
- **Transparency**: Status indicator in navigation bar visible to all users
- **Debugging**: Access to service logs and process information for troubleshooting

## Access

- **URL**: `/services` (in web client)
- **Navigation**: Click the status indicator (🟢/🟡/🔴) in the header navigation bar
- **Status Indicator**: Visible to everyone (authenticated or not) - shows overall system health
- **Page Access**: Requires authentication (any role) - view-only mode for non-admin users
- **Admin Features**: Control buttons (start/stop/restart) and Logs buttons require admin role

## Features

### Service Status Dashboard

The main dashboard displays:

- **Service Cards**: Individual cards for each service showing:
  - Service name and description
  - Status indicator (🟢 healthy, 🟡 degraded, 🔴 unhealthy)
  - Status reason (for non-healthy services)
  - Response time
  - Last check timestamp
  - Process information (PID, uptime, CPU usage, memory usage, threads, open files)
  - Service version
  - Error messages (if any)
  - Manual notes (admin-added notes)

- **Summary Statistics**: Overall counts of healthy, degraded, and unhealthy services

- **Auto-refresh**: Status updates automatically every 15 seconds

- **Manual Refresh**: "🔄 Refresh" button for immediate status check

### Service Status Indicator (Navigation Bar)

- **Location**: Header navigation bar (visible to all users)
- **Visual States**:
  - 🟢 Green: All services healthy
  - 🟡 Amber: One or more services degraded
  - 🔴 Red: One or more services unhealthy
  - ⚪ Gray: Status unknown (loading or error)
- **Tooltip**: Descriptive summary of service status on hover
- **Action**: Clicking opens the Service Management page

### Service Details

Each service card displays:

#### Process Information
- **Process ID (PID)**: Operating system process identifier
- **Uptime**: How long the service has been running (formatted as hours, minutes, seconds)
- **CPU Usage**: Percentage of CPU resources used
- **Memory**: Memory usage in MB and percentage of system memory
- **Threads**: Number of active threads
- **Open Files**: Number of open file descriptors (when available)

#### Service Metadata
- **Version**: Service version number
- **Service Name**: Internal service identifier
- **Description**: Human-readable description of the service's purpose
- **Internal Flag**: Indicates if the service is an internal component (e.g., File Watcher)

#### File Watcher Service
The File Watcher Service (AI Content Management) includes additional metadata:
- **Running Status**: Whether the watcher process is detected
- **Debounce Time**: File change debounce interval in seconds
- **Watched Directory**: Directory being monitored
- **Command**: Command line used to start the watcher

### Logs Viewing

**Permissions:** Admin only

Services with logging enabled (Wiki Service, Auth Service) include a "📋 Logs" button (visible only to admin users) that opens a modal displaying:
- Recent log entries (up to 100 by default)
- Log level (ERROR, WARNING, INFO, DEBUG)
- Timestamp for each entry
- Raw log messages
- Color-coded log levels for easy scanning
- Auto-refresh every 5 seconds when modal is open

### Copy Functionality

**Permissions:** All authenticated users

- **Individual Service Copy**: "📋 Copy" button on each service card copies formatted service information to clipboard
- **Copy All**: "📋 Copy All" button in header copies a comprehensive status report for all services
- **Formatted Output**: Includes all service details in a readable text format suitable for reports or troubleshooting

### Service Control

**Permissions:** Admin only

Services that support programmatic control (Wiki Service, Auth Service, Web Client, File Watcher) include a "⚙️ Control" button (visible only to admin users) that allows:
- **Start**: Start a stopped service
- **Stop**: Gracefully stop a running service
- **Restart**: Stop and then start a service

Control operations are restricted to admin users for security reasons.

## Status Indicators

### 🟢 Green (Healthy)
- Service is fully operational
- All health checks passing
- Response time < 1500ms
- No errors or warnings

**Criteria:**
- Health endpoint returns `200 OK`
- Status is `"healthy"`
- Response time < 1500ms
- No errors in health check response

### 🟡 Yellow (Degraded)
- Service is partially operational
- Performance issues detected
- Response time between 1500ms and 2000ms
- Service functional but slow

**Criteria:**
- Health endpoint returns `200 OK`
- Status is `"healthy"` but response time > 1500ms
- Or service reports `"degraded"` status
- Status reason: "Slow response time (Xms exceeds 1500ms threshold)"

### 🔴 Red (Unhealthy)
- Service is down or critically impaired
- Critical functionality unavailable
- Response time > 2000ms or timeout
- Connection errors or HTTP errors

**Criteria:**
- Health endpoint returns non-200 status
- Status is `"unhealthy"`
- Response time > 2000ms or request timeout
- Connection refused or HTTP errors (404, 500, etc.)
- Status reason provides specific error details

## Monitored Services

### Core Services

1. **Wiki Service**
   - Health endpoint: `GET /api/health`
   - Logs endpoint: `GET /api/admin/logs`
   - Description: Core wiki service providing page management, search, navigation, and content APIs
   - Process information: Self-monitoring (current process)

2. **Auth Service**
   - Health endpoint: `GET /health`
   - Logs endpoint: `GET /api/logs`
   - Description: Authentication and user management service handling login, registration, and JWT tokens
   - Process information: Retrieved from standardized health endpoint response
   - Standard compliance: ✅ Uses `health_check` utility, includes all required fields

3. **File Watcher Service**
   - Health endpoint: Uses Wiki Service health endpoint
   - Description: AI Content Management file watcher that monitors markdown files and syncs changes to the database
   - Type: Internal component (not a separate HTTP service)
   - Process detection: Automatically detects running file watcher process
   - Metadata: Command line, debounce time, watched directory

### Supporting Services

4. **Notification Service**
   - Health endpoint: `GET /health`
   - Description: Handles user notifications and alerts across the platform

5. **Game Server**
   - Health endpoint: `GET /health`
   - Description: Core game server handling game logic, player sessions, and game state

6. **Web Client**
   - Health endpoint: `GET /health` (Vite dev server middleware)
   - Description: Frontend React application providing the user interface for the wiki and platform
   - Process information: Limited in browser context, but includes standard format structure
   - Standard compliance: ✅ Includes all required fields (some values are placeholders in browser context)

7. **Admin Service**
   - Health endpoint: `GET /health`
   - Description: Administrative service for platform management and configuration

8. **Assets Service**
   - Health endpoint: `GET /health`
   - Description: Manages static assets, file uploads, and media storage

9. **Chat Service**
   - Health endpoint: `GET /health`
   - Description: Real-time chat and messaging service for user communication

10. **Leaderboard Service**
    - Health endpoint: `GET /health`
    - Description: Tracks and displays player rankings, scores, and achievements

11. **Presence Service**
    - Health endpoint: `GET /health`
    - Description: Tracks user online/offline status and active sessions

## Implementation

### Health Endpoint Standard

All services implement a standardized health endpoint format as defined in [Health Endpoint Standard](../services/health-endpoint-standard.md). This ensures consistent metadata across all services:

- **Required Fields**: `status`, `service`, `version`, `process_info`
- **Process Info**: PID, uptime, CPU usage, memory usage, threads, open files
- **Optional Fields**: `dependencies` (service dependency status), service-specific metadata

### Backend Service

The `ServiceStatusService` (`services/wiki/app/services/service_status_service.py`) handles:

- **Service Health Checks**: HTTP requests to each service's health endpoint
- **Process Information**: Extracted from standardized health endpoint responses
- **Connection Pooling**: Uses `requests.Session` for improved performance
- **Timeout Management**: Optimized timeouts (0.5s for wiki, 1.0s for others)
- **Status Determination**: Evaluates response time and health endpoint status
- **Error Handling**: Graceful handling of timeouts, connection errors, and HTTP errors
- **Status Reasons**: Provides descriptive reasons for non-healthy statuses
- **Standard Compliance**: Validates and extracts process_info from standardized health responses

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
      "description": "Core wiki service providing page management, search, navigation, and content APIs",
      "status": "healthy",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 5.2,
      "status_reason": null,
      "error": null,
      "process_info": {
        "pid": 12345,
        "uptime_seconds": 3600.5,
        "cpu_percent": 2.5,
        "memory_mb": 150.3,
        "memory_percent": 1.2,
        "threads": 8,
        "open_files": 15
      },
      "version": "1.0.0",
      "service_name": "wiki",
      "details": {
        "status": "healthy",
        "service": "wiki"
      },
      "manual_notes": null,
      "is_internal": false
    },
    "auth": {
      "name": "Auth Service",
      "description": "Authentication and user management service handling login, registration, and JWT tokens",
      "status": "degraded",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 1107.3,
      "status_reason": "Slow response time (1107ms exceeds 1500ms threshold)",
      "error": null,
      "process_info": {
        "pid": 67890,
        "uptime_seconds": 7200.0,
        "cpu_percent": 0.5,
        "memory_mb": 87.8,
        "memory_percent": 0.6,
        "threads": 5,
        "open_files": 2
      },
      "version": "1.0.0",
      "service_name": "auth",
      "details": {
        "status": "healthy",
        "service": "auth"
      },
      "manual_notes": null,
      "is_internal": false
    },
    "file-watcher": {
      "name": "File Watcher Service",
      "description": "AI Content Management file watcher that monitors markdown files and syncs changes to the database",
      "status": "healthy",
      "last_check": "2024-01-01T12:00:00Z",
      "response_time_ms": 5.2,
      "status_reason": null,
      "error": null,
      "process_info": {
        "pid": 11111,
        "uptime_seconds": 1800.0,
        "cpu_percent": 0.1,
        "memory_mb": 45.2,
        "memory_percent": 0.3,
        "threads": 3,
        "open_files": 5
      },
      "watcher_metadata": {
        "command": "python -m app.sync watch",
        "debounce_seconds": 1.0,
        "watched_directory": "/path/to/data/pages"
      },
      "is_running": true,
      "is_internal": true,
      "details": {
        "status": "healthy",
        "service": "wiki"
      }
    }
  },
  "last_updated": "2024-01-01T12:00:00Z"
}
```

#### Refresh Service Status
```
POST /api/admin/service-status/refresh
```

Triggers an immediate health check of all services.

#### Get Service Logs (Wiki Service)
```
GET /api/admin/logs?limit=100&level=ERROR
```

**Query Parameters:**
- `limit` (optional): Maximum number of log entries (default: 100, max: 500)
- `level` (optional): Filter by log level (ERROR, WARNING, INFO, DEBUG)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00.123456",
      "level": "ERROR",
      "message": "Database connection failed",
      "raw_message": "Database connection failed",
      "pathname": "/app/services/db.py",
      "lineno": 42,
      "funcName": "connect",
      "process": 12345,
      "thread": 140234567890,
      "threadName": "MainThread"
    }
  ]
}
```

#### Get Service Logs (Auth Service)
```
GET /api/logs?limit=100&level=ERROR
```

Same format as Wiki Service logs.

### Frontend Components

- **ServiceManagementPage** (`client/src/pages/ServiceManagementPage.jsx`): Main dashboard component
- **ServiceStatusIndicator** (`client/src/components/common/ServiceStatusIndicator.jsx`): Navigation bar status indicator
- **ServiceLogsButton** (embedded in ServiceManagementPage): Logs viewing modal
- **useServiceStatus** (`client/src/services/api/services.js`): React Query hook for service status
- **useServiceLogs** (`client/src/services/api/services.js`): React Query hook for service logs

### Auto-Refresh Configuration

- **Service Status**: Refreshes every 15 seconds when page is active
- **Service Logs**: Refreshes every 5 seconds when logs modal is open
- **Background Refetching**: Disabled when browser tab is in background (saves resources)
- **Manual Refresh**: Available via "🔄 Refresh" button

## Status Determination Logic

### Response Time Thresholds

- **Healthy**: Response time < 1500ms
- **Degraded**: Response time between 1500ms and 2000ms
- **Unhealthy**: Response time > 2000ms or timeout

### Status Reasons

When a service is not healthy, a descriptive reason is provided:

- **Slow Response Time**: "Slow response time (Xms exceeds 1500ms threshold)" or "Slow response time (Xms exceeds 2000ms threshold)"
- **Timeout**: "Request timed out after Xs - service may be overloaded or unreachable"
- **Connection Error**: "Connection refused - service may be down or not listening on the expected port"
- **HTTP Error**: "HTTP 404 error - service may be experiencing issues" or "Health endpoint not found (404) - service may be misconfigured"
- **Service-Reported**: Uses reason from service's health endpoint if available

## Performance Optimizations

1. **Connection Pooling**: Uses `requests.Session` to reuse HTTP connections
2. **Optimized Timeouts**: Short timeouts (0.5s for wiki, 1.0s for others) to prevent long waits
3. **Non-blocking Process Info**: Uses `psutil.Process.oneshot()` and `cpu_percent(interval=None)` for fast health checks
4. **Windows Optimizations**: Skips slow `open_files()` call on Windows
5. **Parallel Checks**: Services checked independently (wiki checked first, then others)

## Error Handling

- **Timeout**: Returns unhealthy status with timeout reason
- **Connection Refused**: Returns unhealthy status with connection error reason
- **HTTP Errors**: Returns unhealthy status with HTTP error details
- **Non-JSON Response**: Returns degraded status for HTML responses (web client), unhealthy for other non-JSON
- **401/403 Responses**: Treated as healthy (service is up, just needs authentication)
- **Missing Process Info**: Gracefully handles missing `psutil` or process access errors

## Access Control

- **Current**: Temporarily available to all users (for development)
- **Future**: Will require admin role for full access
- **Status Indicator**: Visible to all users in navigation bar
- **Service Management Page**: Will require admin role (currently open to all)

## Future Enhancements

- **Service Control**: Start/stop/restart services (requires backend implementation)
- **Historical Data**: Track status over time with graphs
- **Alerting**: Notify admins when services go down
- **Metrics Dashboard**: Response time graphs, uptime percentages
- **Service Dependencies Graph**: Visual representation of service dependencies
- **Incident Management**: Link to incident reports
- **Scheduled Checks**: Configurable check intervals per service
- **Filtering and Sorting**: Filter services by status, sort by various metrics
- **Export Functionality**: Export status reports in various formats (JSON, CSV, PDF)

## Related Documentation

- [Service Architecture](../services/service-architecture.md) - Service communication and health checks
- [Service Dependencies](../services/service-dependencies.md) - Service relationships
- [Wiki Admin Dashboard](wiki-admin-dashboard.md) - Admin features
- [Wiki Service README](../../services/wiki/README.md) - Wiki service setup and API
