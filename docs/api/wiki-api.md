# Wiki Service API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication

All endpoints (except public viewing) require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Pages

#### List Pages
```
GET /api/pages
```

**Query Parameters:**
- `section` (optional): Filter by section name
- `parent_id` (optional): Filter by parent page ID
- `search` (optional): Search term for title/content
- `status` (optional): Filter by status (`published`, `draft`) - defaults to `published` for non-creators
- `include_drafts` (optional, default: false): Include draft pages (only for creator or admin)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "pages": [
    {
      "id": "uuid",
      "title": "Page Title",
      "slug": "page-title",
      "parent_id": "uuid-or-null",
      "section": "section-name",
      "order": 1,
      "status": "published",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "created_by": "user-id",
      "updated_by": "user-id"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

**Note:** Draft pages are filtered out for non-creators and non-admins unless `include_drafts=true` is specified (and user has permission).

**Permissions:** Public (viewer) - but drafts filtered by permission

---

#### Get Page
```
GET /api/pages/{page_id}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Page Title",
  "slug": "page-slug",
  "content": "# Markdown content...",
  "html_content": "<h1>HTML content...</h1>",
  "parent_id": "uuid-or-null",
  "section": "section-name",
  "order": 1,
  "status": "published",
  "word_count": 1250,
  "content_size_kb": 45.2,
  "table_of_contents": [
    {
      "level": 2,
      "text": "Section Title",
      "anchor": "section-title"
    }
  ],
  "forward_links": [
    {
      "page_id": "uuid",
      "title": "Linked Page",
      "slug": "linked-page"
    }
  ],
  "backlinks": [
    {
      "page_id": "uuid",
      "title": "Page That Links Here",
      "slug": "page-that-links-here"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": {
    "id": "user-id",
    "username": "author"
  },
  "updated_by": {
    "id": "user-id",
    "username": "editor"
  }
}
```

**Note:** Draft pages return 404 for non-creators and non-admins.

**Permissions:** Public (viewer) for published pages, Creator/Admin for drafts

---

#### Create Page
```
POST /api/pages
```

**Request Body:**
```json
{
  "title": "New Page Title",
  "slug": "new-page-slug",  // Optional: auto-generated if not provided
  "content": "# Markdown content...",
  "parent_id": "uuid-or-null",
  "section": "section-name",  // Writers can create new sections
  "order": 1,
  "status": "published"  // or "draft"
}
```

**Note:** Slug is auto-generated from title if not provided. Must be unique. Writers can create new sections.

**Response:**
```json
{
  "id": "uuid",
  "title": "New Page Title",
  "slug": "new-page-slug",
  "content": "# Markdown content...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Writer, Admin

---

#### Update Page
```
PUT /api/pages/{page_id}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "slug": "updated-slug",  // Optional: only if changing
  "content": "# Updated markdown...",
  "parent_id": "uuid-or-null",
  "section": "section-name",
  "order": 1,
  "status": "published"  // or "draft"
}
```

**Note:** Slug changes are validated for uniqueness. Creates new version automatically.

**Response:**
```json
{
  "id": "uuid",
  "title": "Updated Title",
  "content": "# Updated markdown...",
  "updated_at": "2024-01-01T00:00:00Z",
  "version": 2
}
```

**Permissions:** Writer, Admin

---

#### Delete Page
```
DELETE /api/pages/{page_id}
```

**Response:**
```json
{
  "message": "Page deleted successfully",
  "orphaned_pages": [
    {
      "id": "uuid",
      "title": "Orphaned Page",
      "moved_to_orphanage": true
    }
  ],
  "orphaned_count": 3,
  "reassign_option": true
}
```

**Note:** If page has children, they are moved to orphanage. Response includes list of orphaned pages and option to reassign immediately.

**Permissions:** Admin (can delete any), Writer (can delete own pages)

---

### Comments

#### Get Comments for Page
```
GET /api/pages/{page_id}/comments
```

**Query Parameters:**
- `include_replies` (optional, default: true): Include threaded replies

**Response:**
```json
{
  "comments": [
    {
      "id": "uuid",
      "user": {
        "id": "user-id",
        "username": "commenter"
      },
      "content": "Comment text",
      "is_recommendation": false,
      "parent_comment_id": null,
      "replies": [
        {
          "id": "uuid",
          "user": {
            "id": "user-id",
            "username": "replier"
          },
          "content": "Reply text",
          "parent_comment_id": "parent-uuid"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Permissions:** Public (viewer)

---

#### Create Comment
```
POST /api/pages/{page_id}/comments
```

**Request Body:**
```json
{
  "content": "Comment text",
  "is_recommendation": false,
  "parent_comment_id": "uuid-or-null"
}
```

**Validation:**
- If `parent_comment_id` is provided, system checks thread depth
- Maximum depth: 5 levels
- If at max depth, returns 400 error: "Maximum comment thread depth (5) reached"

**Response:**
```json
{
  "id": "uuid",
  "content": "Comment text",
  "is_recommendation": false,
  "parent_comment_id": "uuid-or-null",
  "thread_depth": 2,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Response (max depth):**
```json
{
  "error": "Maximum comment thread depth reached",
  "max_depth": 5,
  "current_depth": 5
}
```

**Permissions:** Player, Writer, Admin

---

#### Update Comment
```
PUT /api/comments/{comment_id}
```

**Request Body:**
```json
{
  "content": "Updated comment text"
}
```

**Response:**
```json
{
  "id": "uuid",
  "content": "Updated comment text",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Permissions:** Owner, Admin

---

#### Delete Comment
```
DELETE /api/comments/{comment_id}
```

**Response:**
```json
{
  "message": "Comment deleted successfully"
}
```

**Permissions:** Owner, Admin

---

### Search and Index

#### Search Pages
```
GET /api/search
```

**Query Parameters:**
- `q` (required): Search query
- `section` (optional): Filter by section
- `include_drafts` (optional, default: false): Include draft pages (only for creator or admin)
- `limit` (optional): Number of results (default: 20)

**Response:**
```json
{
  "results": [
    {
      "page_id": "uuid",
      "title": "Page Title",
      "slug": "page-slug",
      "section": "section-name",
      "status": "published",
      "snippet": "Relevant text snippet...",
      "relevance_score": 0.95
    }
  ],
  "total": 10,
  "query": "search term"
}
```

**Note:** 
- Uses PostgreSQL full-text search with relevance ranking
- Draft pages excluded from results unless `include_drafts=true` and user has permission
- Search indexes both full-text content and manually tagged keywords

**Permissions:** Public (viewer) - but drafts filtered by permission

---

#### Get Master Index
```
GET /api/index
```

**Query Parameters:**
- `letter` (optional): Filter by starting letter
- `section` (optional): Filter by section

**Response:**
```json
{
  "index": {
    "A": [
      {
        "page_id": "uuid",
        "title": "Article Title",
        "slug": "article-slug",
        "section": "section-name"
      }
    ],
    "B": [...]
  }
}
```

**Permissions:** Public (viewer)

---

### Navigation

#### Get Page Hierarchy
```
GET /api/navigation
```

**Response:**
```json
{
  "tree": [
    {
      "id": "uuid",
      "title": "Top Level Page",
      "slug": "top-level",
      "status": "published",
      "children": [
        {
          "id": "uuid",
          "title": "Child Page",
          "slug": "child-page",
          "status": "published",
          "children": []
        }
      ]
    }
  ]
}
```

**Note:** Draft pages are excluded from navigation tree for non-creators and non-admins.

**Permissions:** Public (viewer) - but drafts filtered by permission

---

#### Get Breadcrumb
```
GET /api/pages/{page_id}/breadcrumb
```

**Response:**
```json
{
  "breadcrumb": [
    {
      "id": "uuid",
      "title": "Root Page",
      "slug": "root"
    },
    {
      "id": "uuid",
      "title": "Parent Page",
      "slug": "parent"
    },
    {
      "id": "uuid",
      "title": "Current Page",
      "slug": "current"
    }
  ]
}
```

**Permissions:** Public (viewer)

---

#### Get Previous/Next Pages
```
GET /api/pages/{page_id}/navigation
```

**Response:**
```json
{
  "previous": {
    "id": "uuid",
    "title": "Previous Page",
    "slug": "previous-page"
  },
  "next": {
    "id": "uuid",
    "title": "Next Page",
    "slug": "next-page"
  }
}
```

**Permissions:** Public (viewer)

---

### File Upload

#### Upload Image
```
POST /api/upload/image
```

**Request:** multipart/form-data
- `file`: Image file
- `page_id` (optional): Associate with specific page

**Response:**
```json
{
  "url": "/uploads/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "original_filename": "my-image.jpg",
  "size": 12345,
  "mime_type": "image/jpeg",
  "page_id": "uuid-or-null"
}
```

**Note:** Filename is UUID-based for storage, original filename stored in metadata.

**Permissions:** Writer, Admin

---

### Orphanage Management

#### Get Orphanage
```
GET /api/orphanage
```

**Response:**
```json
{
  "orphanage_id": "uuid",
  "pages": [
    {
      "id": "uuid",
      "title": "Orphaned Page",
      "slug": "orphaned-page",
      "orphaned_from": {
        "id": "uuid",
        "title": "Deleted Parent"
      },
      "orphaned_at": "2024-01-15T10:30:00Z"
    }
  ],
  "grouped_by_parent": {
    "parent-uuid-1": [...],
    "parent-uuid-2": [...]
  }
}
```

**Permissions:** Public (viewer)

---

#### Reassign Orphaned Pages
```
POST /api/orphanage/reassign
```

**Request Body:**
```json
{
  "page_ids": ["uuid1", "uuid2"],
  "new_parent_id": "uuid",
  "reassign_all": false
}
```

**Response:**
```json
{
  "reassigned": 2,
  "remaining_in_orphanage": 5
}
```

**Permissions:** Admin (only admins can manage orphanage)

---

#### Clear Orphanage
```
POST /api/orphanage/clear
```

**Request Body:**
```json
{
  "reassign_to": "uuid"  // Optional: reassign all to this parent before clearing
}
```

**Response:**
```json
{
  "message": "Orphanage cleared successfully",
  "reassigned_count": 5,  // If reassign_to was provided
  "deleted_count": 0  // Pages deleted (if any, should be 0)
}
```

**Note:** If `reassign_to` is provided, all orphaned pages are reassigned to that parent before clearing. Otherwise, pages remain orphaned but orphanage container is cleared.

**Permissions:** Admin only

---

### Section Extraction

#### Extract Selection to New Page
```
POST /api/pages/{page_id}/extract
```

**Request Body:**
```json
{
  "selection_start": 100,
  "selection_end": 500,
  "new_title": "Extracted Section",
  "new_slug": "extracted-section",
  "parent_id": "uuid",
  "section": "section-name",
  "replace_with_link": true
}
```

**Response:**
```json
{
  "new_page": {
    "id": "uuid",
    "title": "Extracted Section",
    "slug": "extracted-section"
  },
  "original_page": {
    "id": "uuid",
    "version": 6
  }
}
```

**Permissions:** Writer, Admin

---

#### Extract Heading Section
```
POST /api/pages/{page_id}/extract-heading
```

**Request Body:**
```json
{
  "heading_text": "Section Title",
  "heading_level": 2,
  "new_title": "Extracted Section",
  "new_slug": "extracted-section",
  "parent_id": "uuid",
  "section": "section-name",
  "promote_as": "child"
}
```

**Response:**
```json
{
  "new_page": {...},
  "original_page": {...}
}
```

**Permissions:** Writer, Admin

---

#### Promote Section from TOC
```
POST /api/pages/{page_id}/promote-section
```

**Request Body:**
```json
{
  "heading_anchor": "section-title",
  "promote_as": "child",
  "new_title": "Promoted Section",
  "new_slug": "promoted-section",
  "section": "section-name"
}
```

**Response:**
```json
{
  "new_page": {...},
  "original_page": {...}
}
```

**Permissions:** Writer, Admin

---

### Admin Dashboard

#### Get Dashboard Statistics
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

**Permissions:** Admin

---

#### Get Size Distribution
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

**Permissions:** Admin

---

#### Configure File Upload Size
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

**Response:**
```json
{
  "max_size_mb": 10,
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Permissions:** Admin

---

#### Configure Page Size Limit
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

**Response:**
```json
{
  "max_size_kb": 500,
  "resolution_due_date": "2024-02-01T00:00:00Z",
  "oversized_pages_count": 5,
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Permissions:** Admin

---

#### Get Oversized Pages
```
GET /api/admin/oversized-pages
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_progress, resolved)
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "pages": [
    {
      "id": "uuid",
      "title": "Large Page",
      "slug": "large-page",
      "current_size_kb": 750,
      "max_size_kb": 500,
      "word_count": 5000,
      "authors": [
        {
          "id": "uuid",
          "username": "writer"
        }
      ],
      "due_date": "2024-02-01T00:00:00Z",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5
}
```

**Permissions:** Admin

---

#### Update Oversized Page Status
```
PUT /api/admin/oversized-pages/{page_id}/status
```

**Request Body:**
```json
{
  "status": "in_progress",
  "extend_due_date": "2024-02-15T00:00:00Z"
}
```

**Response:**
```json
{
  "page_id": "uuid",
  "status": "in_progress",
  "due_date": "2024-02-15T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Permissions:** Admin

---

## Error Responses

All endpoints may return the following error responses:

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
  "error": "Insufficient permissions",
  "required_role": "writer"
}
```

### 404 Not Found
```json
{
  "error": "Page not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

