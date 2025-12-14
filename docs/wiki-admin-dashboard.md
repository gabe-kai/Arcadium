# Wiki Admin Dashboard

## Overview

The Admin Dashboard provides system configuration, monitoring, and management tools for wiki administrators.

## Dashboard Sections

### 1. File Upload Configuration

#### Maximum File Upload Size
- **Preset Options**: 1MB, 2MB, 5MB, 10MB
- **Custom Size**: Admin can enter custom size in MB
- **Current Setting**: Displayed prominently
- **Apply Button**: Saves configuration

**UI:**
```
Maximum File Upload Size
○ 1 MB
○ 2 MB
○ 5 MB
● 10 MB
○ Custom: [____] MB

[Save Configuration]
```

### 2. Page Size Monitoring

#### Size Distribution Charts

**Chart 1: Pages by Size (KB)**
- Bar chart showing page count in size buckets
- Buckets: 0-10KB, 10-50KB, 50-100KB, 100-500KB, 500KB-1MB, 1MB+
- Hover shows exact counts
- Click to filter pages in that bucket

**Chart 2: Pages by Word Count**
- Bar chart showing page count in word count buckets
- Buckets: 0-500, 500-1000, 1000-2500, 2500-5000, 5000-10000, 10000+
- Hover shows exact counts
- Click to filter pages in that bucket

**Note**: Images do NOT count toward page size (they are links only)

#### Maximum Page Size Configuration

**Setting:**
```
Maximum Page Size
[____] KB

[Set Maximum] [Remove Limit]
```

**Oversized Pages Management:**
When maximum is set or lowered:
1. System identifies pages exceeding limit
2. Admin must set a resolution due date
3. Oversized pages are flagged
4. Page authors are notified via internal messaging
5. Pages appear in "Oversized Pages" list

**Oversized Pages List:**
- Table showing:
  - Page title
  - Current size (KB)
  - Word count
  - Author(s)
  - Due date
  - Status (pending, in progress, resolved)
- Filter by status
- Sort by due date, size, etc.
- Bulk actions

### 3. System Statistics

- Total pages
- Total sections
- Total users (by role)
- Total comments
- Storage usage
- Recent activity

### 4. Orphanage Management

- View all orphaned pages
- Bulk reassignment tools
- Clear orphanage (with reassignment option)

## Oversized Pages Workflow

### When Maximum is Set/Lowered

1. Admin sets maximum page size
2. System scans all pages
3. Identifies pages exceeding limit
4. Admin sets resolution due date
5. System creates `OversizedPageNotification` records
6. Internal messages sent to page authors
7. Oversized pages flagged in UI

### Notification System

**Internal Messaging:**
- Message to each page author:
  - Subject: "Page Size Limit Exceeded"
  - Content: "Your page '[Title]' exceeds the maximum size of X KB. Please reduce it to under X KB by [Due Date]."
  - Link to page
  - Link to editor

**Page Indicators:**
- Oversized pages show warning badge
- Editor shows size warning
- Size displayed prominently

### Resolution Tracking

- Authors can mark as "In Progress"
- Authors can mark as "Resolved" (when under limit)
- Admin can extend due date
- Admin can mark as resolved manually
- System auto-resolves when page size drops below limit

## API Endpoints

### Get Dashboard Stats
```
GET /api/admin/dashboard/stats
```

**Response:**
```json
{
  "total_pages": 150,
  "total_sections": 12,
  "total_users": {
    "viewers": 50,
    "players": 30,
    "writers": 10,
    "admins": 2
  },
  "total_comments": 500,
  "storage_usage_mb": 125.5,
  "recent_activity": [...]
}
```

### Get Size Distribution
```
GET /api/admin/dashboard/size-distribution
```

**Response:**
```json
{
  "by_size_kb": {
    "0-10": 50,
    "10-50": 60,
    "50-100": 25,
    "100-500": 10,
    "500-1000": 4,
    "1000+": 1
  },
  "by_word_count": {
    "0-500": 40,
    "500-1000": 55,
    "1000-2500": 35,
    "2500-5000": 15,
    "5000-10000": 4,
    "10000+": 1
  }
}
```

### Configure File Upload Size
```
POST /api/admin/config/upload-size
```

**Request Body:**
```json
{
  "max_size_mb": 10,
  "is_custom": false
}
```

### Configure Page Size Limit
```
POST /api/admin/config/page-size
```

**Request Body:**
```json
{
  "max_size_kb": 500,
  "resolution_due_date": "2024-02-01T00:00:00Z"
}
```

### Get Oversized Pages
```
GET /api/admin/oversized-pages
```

**Response:**
```json
{
  "pages": [
    {
      "id": "uuid",
      "title": "Large Page",
      "current_size_kb": 750,
      "max_size_kb": 500,
      "word_count": 5000,
      "authors": [...],
      "due_date": "2024-02-01T00:00:00Z",
      "status": "pending"
    }
  ]
}
```

### Update Oversized Page Status
```
PUT /api/admin/oversized-pages/{page_id}/status
```

**Request Body:**
```json
{
  "status": "in_progress",
  "extend_due_date": "2024-02-15T00:00:00Z"  // Optional
}
```

## Implementation Notes

### Size Calculation
- Page size = Markdown content size (in KB)
- Word count = Text content word count
- Images excluded (they are links only)
- Calculated on save, cached in database

### Monitoring
- Charts update in real-time
- Background job recalculates sizes periodically
- Alerts when new oversized pages detected

### Performance
- Cache size distribution data
- Lazy-load oversized pages list
- Paginate large result sets

