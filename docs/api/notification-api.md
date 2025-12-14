# Notification Service API Documentation

## Overview

The Notification Service provides internal messaging and notification capabilities for the Arcadium platform. It handles system notifications, user-to-user messages, and service-to-user communications.

## Base URL
```
http://localhost:8006/api
```

**Note:** This service may be integrated into the Chat Service or exist as a separate service. The API design supports both approaches.

## Authentication

All endpoints require authentication via JWT token:
```
Authorization: Bearer <token>
```

## Endpoints

### Internal Messaging

#### Send Internal Message
```
POST /api/notifications/send
```

**Request Body:**
```json
{
  "recipient_ids": ["uuid1", "uuid2"],
  "subject": "Page Size Limit Exceeded",
  "content": "Your page 'Combat Mechanics' exceeds the maximum size...",
  "type": "system",  // "system", "user", "warning", "info"
  "action_url": "/wiki/pages/combat-mechanics",  // Optional: link to relevant page
  "metadata": {
    "page_id": "uuid",
    "notification_type": "oversized_page"
  }
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "sent_to": 2,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** System services (with service token) or Admin

---

#### Get User Notifications
```
GET /api/notifications
```

**Query Parameters:**
- `unread_only` (optional, default: false): Only return unread notifications
- `type` (optional): Filter by type (system, user, warning, info)
- `grouped` (optional, default: true): Return grouped notifications
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "subject": "Page Size Limit Exceeded",
      "content": "Your page 'Combat Mechanics' exceeds...",
      "type": "warning",
      "read": false,
      "action_url": "/wiki/pages/combat-mechanics",
      "metadata": {
        "page_id": "uuid"
      },
      "group_id": "uuid",  // For grouped notifications
      "group_count": 1,  // Number of notifications in group
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "grouped_notifications": [
    {
      "group_id": "uuid",
      "subject": "Page Size Limit Exceeded",
      "type": "warning",
      "count": 5,
      "latest": "2024-01-01T00:00:00Z",
      "read": false
    }
  ],
  "unread_count": 5,
  "total": 20
}
```

**Note:** For admin users, includes shared admin notifications. If one admin reads/deletes, all admins see the change.

**Permissions:** Self (own notifications + admin shared notifications)

---

#### Mark Notification as Read
```
PUT /api/notifications/{notification_id}/read
```

**Response:**
```json
{
  "id": "uuid",
  "read": true,
  "read_at": "2024-01-01T00:00:00Z"
}
```

**Note:** For admin-shared notifications, marking as read affects all admins.

**Permissions:** Self (own notifications + admin shared notifications)

---

#### Mark All as Read
```
PUT /api/notifications/read-all
```

**Response:**
```json
{
  "marked_read": 5,
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Self

---

#### Delete Notification
```
DELETE /api/notifications/{notification_id}
```

**Response:**
```json
{
  "message": "Notification deleted"
}
```

**Note:** For admin-shared notifications, deletion affects all admins.

**Permissions:** Self (own notifications + admin shared notifications)

---

#### Get Grouped Notifications
```
GET /api/notifications/grouped
```

**Query Parameters:**
- `group_id` (optional): Get notifications for specific group
- `type` (optional): Filter by type

**Response:**
```json
{
  "group_id": "uuid",
  "notifications": [
    {
      "id": "uuid",
      "subject": "Page Size Limit Exceeded",
      "content": "...",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 5
}
```

**Permissions:** Self

---

### System Notifications

#### Create System Notification
```
POST /api/notifications/system
```

**Request Body:**
```json
{
  "recipient_ids": ["uuid1", "uuid2"],
  "subject": "System Maintenance",
  "content": "The wiki will be under maintenance...",
  "type": "info",
  "priority": "normal"  // "low", "normal", "high", "urgent"
}
```

**Response:**
```json
{
  "notification_id": "uuid",
  "sent_to": 2
}
```

**Permissions:** System services (with service token) or Admin

---

## Integration with Wiki Service

### Wiki Service Requirements

The Wiki Service uses the Notification Service for:

1. **Oversized Page Notifications**
   - When page size limit is set/lowered
   - Notify page authors about oversized pages
   - Include due date and page link

2. **Notification Format**
   ```json
   {
     "recipient_ids": ["author-uuid-1", "author-uuid-2"],
     "subject": "Page Size Limit Exceeded",
     "content": "Your page '[Page Title]' exceeds the maximum size of X KB. Please reduce it to under X KB by [Due Date].",
     "type": "warning",
     "action_url": "/wiki/pages/{page-slug}",
     "metadata": {
       "page_id": "uuid",
       "current_size_kb": 750,
       "max_size_kb": 500,
       "due_date": "2024-02-01T00:00:00Z",
       "notification_type": "oversized_page"
     }
   }
   ```

3. **Notification Types Used by Wiki**
   - `warning`: Oversized pages, due date approaching
   - `info`: General wiki updates, system messages
   - `system`: Automated notifications

### Service-to-Service Communication

Wiki Service calls Notification Service using:
- Service authentication token (separate from user JWT)
- Direct HTTP calls to notification endpoints
- Error handling for notification failures (non-blocking)

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

## Database Schema

### Notifications Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL,
    sender_id UUID,  -- NULL for system notifications
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    action_url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_read ON notifications(recipient_id, read);
CREATE INDEX idx_notifications_type ON notifications(type);
```

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
  "error": "Authentication required"
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
  "error": "Notification not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

