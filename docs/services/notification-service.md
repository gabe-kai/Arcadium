# Notification Service Specification

## Overview

The Notification Service provides internal messaging and notification capabilities for the Arcadium platform. It handles system notifications, user-to-user messages, and service-to-service communications.

## Core Responsibilities

1. **Internal Messaging**
   - Send notifications to users
   - User notification inbox
   - Read/unread status tracking
   - Notification deletion

2. **System Notifications**
   - Service-to-user notifications
   - Automated system messages
   - Priority-based delivery

3. **Notification Management**
   - Mark as read/unread
   - Filter and search
   - Notification preferences (future)

## Integration Points

### Wiki Service Integration

The Wiki Service uses Notification Service for:

1. **Oversized Page Notifications**
   - When admin sets/lowers page size limit
   - Notify all page authors about oversized pages
   - Include due date and resolution requirements
   - Link to affected pages

2. **Notification Format**
   ```json
   {
     "recipient_ids": ["author-uuid"],
     "subject": "Page Size Limit Exceeded",
     "content": "Your page '[Title]' exceeds the maximum size...",
     "type": "warning",
     "action_url": "/wiki/pages/{slug}",
     "metadata": {
       "page_id": "uuid",
       "notification_type": "oversized_page"
     }
   }
   ```

3. **Service Authentication**
   - Wiki Service uses service token for authentication
   - Separate from user JWT tokens
   - Allows services to send notifications on behalf of system

## Notification Types

### Type Definitions

- **system**: System-generated notifications (maintenance, updates)
- **user**: User-to-user messages
- **warning**: Important warnings requiring action
- **info**: Informational messages

### Priority Levels

- **low**: Non-urgent notifications
- **normal**: Standard priority
- **high**: Important notifications
- **urgent**: Critical, requires immediate attention

## Notification Grouping

### Grouped Notifications
- Similar notifications can be grouped together
- Grouping criteria:
  - Same type and subject
  - Same time period (within 1 hour)
  - Same source/service
- Grouped notifications show count: "5 new warnings"
- Expand to see individual notifications

### Admin Shared Notifications
- **Special Behavior**: Admin notifications are shared across all admins
- If one admin reads a notification, it's marked as read for all admins
- If one admin deletes a notification, it's deleted for all admins
- Applies to system notifications and admin-specific notifications
- Regular user notifications remain private

## Notification Delivery

### Delivery Method
- **Initial Load**: Client polls `GET /api/notifications` on page load
- **Updates**: Polling every 30 seconds (configurable)
- **Future**: WebSocket for real-time push notifications

### Notification Retention
- Notifications kept indefinitely (no auto-deletion)
- Users can manually delete notifications
- Old notifications can be archived (future enhancement)

## Notification Limits

- **No limits** on number of notifications per user
- **No limits** on sending notifications
- Rate limiting handled at service level if needed

## API Endpoints

See [Notification Service API Documentation](../api/notification-api.md) for complete endpoint specifications.

### Key Endpoints

- `POST /api/notifications/send` - Send notification to users
- `GET /api/notifications` - Get user's notifications
- `PUT /api/notifications/{id}/read` - Mark as read
- `POST /api/notifications/system` - Create system notification

## Database Schema

### Notifications Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID,  -- NULL for admin-shared notifications
    recipient_role VARCHAR(20),  -- For role-based notifications (e.g., 'admin')
    sender_id UUID,  -- NULL for system notifications
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    read BOOLEAN DEFAULT FALSE,
    read_by UUID[],  -- Array of user IDs who have read (for admin-shared)
    read_at TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_by UUID[],  -- Array of user IDs who have deleted (for admin-shared)
    deleted_at TIMESTAMP,
    action_url VARCHAR(500),
    metadata JSONB,
    group_id UUID,  -- For grouping related notifications
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_role ON notifications(recipient_role);
CREATE INDEX idx_notifications_read ON notifications(recipient_id, read) WHERE recipient_id IS NOT NULL;
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX idx_notifications_group ON notifications(group_id);
CREATE INDEX idx_notifications_deleted ON notifications(deleted) WHERE deleted = FALSE;
```

### Admin Notification Reads Table
```sql
CREATE TABLE admin_notification_reads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    admin_id UUID NOT NULL,
    read_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(notification_id, admin_id)
);

CREATE INDEX idx_admin_reads_notification ON admin_notification_reads(notification_id);
CREATE INDEX idx_admin_reads_admin ON admin_notification_reads(admin_id);
```

## Service Architecture

### Technology Stack
- **Language**: Python/Flask (matches other services)
- **Database**: PostgreSQL
- **Authentication**: JWT tokens (user) + service tokens

### Service Structure
```
services/notification/
  app/
    __init__.py
    routes/
      notification_routes.py
    models/
      notification.py
    services/
      notification_service.py
      delivery_service.py
    utils/
      validators.py
  tests/
  requirements.txt
  Dockerfile
  README.md
```

## Service-to-Service Communication

### Authentication

Services authenticate using service tokens (JWT with service claims):
```
Authorization: Service-Token <service-token>
```

Service tokens:
- Generated by Auth Service during service setup
- Long-lived (90 days expiration)
- Stored in service environment variables
- Validated by Auth Service or shared validation library

### Error Handling

- Notification failures are non-blocking
- Wiki Service should log but not fail if notification fails
- Retry mechanism: 3 attempts with exponential backoff
- Failed notifications logged for manual review
- Timeout: 5 seconds for notification requests

## Future Enhancements

- Email notifications
- Push notifications
- Notification preferences per user
- Notification templates
- Batch notification sending
- Notification scheduling
- Read receipts
- Notification channels (in-app, email, push)

## Alternative: Integration with Chat Service

If Notification Service is integrated into Chat Service:
- Use same database and service
- Separate endpoints for notifications vs chat
- Shared user inbox for messages and notifications
- Unified notification center in UI
