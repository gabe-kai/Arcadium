# Wiki Orphanage System

## Overview

When a page with child pages is deleted, the orphanage system automatically collects orphaned pages into a special "Orphanage" container, allowing them to be managed as a group rather than individually.

## Orphanage Container

### System Page
- **Special page**: System-created page with slug `_orphanage`
- **Title**: "Orphaned Pages"
- **Parent**: `null` (top-level)
- **Purpose**: Temporary container for orphaned pages
- **Visibility**: Visible to all users, but clearly marked as system page

### Orphanage Behavior

When a page is deleted:
1. System identifies all child pages (direct children only)
2. All child pages are moved to the orphanage (parent_id set to orphanage UUID)
3. `is_orphaned` flag set to `true` on each orphaned page
4. `orphaned_from` field stores the original parent's ID
5. User is notified: "X pages have been moved to the Orphanage"
6. User is presented with options:
   - Leave in orphanage (default)
   - Reassign to new parent immediately (opens reassignment dialog)

## Reassignment Options

### Immediate Reassignment
When user chooses to reassign immediately:
- Dialog opens showing all orphaned pages
- User can select a new parent for the group
- All orphaned pages are moved to the new parent at once
- Orphanage is cleared (if all pages reassigned)

### Manual Reassignment
Users can also:
- Navigate to orphanage page
- View all orphaned pages
- Reassign individual pages or groups
- Filter by original parent (using `orphaned_from`)

## Orphanage UI

### Orphanage Page View
- List of all orphaned pages
- Grouped by original parent (if multiple deletions)
- Show original parent name (from `orphaned_from`)
- Bulk reassignment options
- Individual page actions

### Notification
When pages are orphaned:
- Toast notification: "X pages moved to Orphanage"
- Link to orphanage page
- Option to reassign immediately

### Visual Indicators
- Orphaned pages show special icon/badge
- Orphanage page clearly marked as system page
- Breadcrumb shows "Orphaned Pages" when viewing orphanage

## Database Schema

### Pages Table Addition
```sql
ALTER TABLE pages ADD COLUMN is_orphaned BOOLEAN DEFAULT FALSE;
ALTER TABLE pages ADD COLUMN orphaned_from UUID REFERENCES pages(id);
CREATE INDEX idx_pages_orphaned ON pages(is_orphaned) WHERE is_orphaned = TRUE;
```

### Orphanage System Page
- **Creation Trigger**: Created automatically when first page with children is deleted
- **Creation Process**:
  1. Check if orphanage page exists: `SELECT * FROM pages WHERE slug='_orphanage'`
  2. If not exists:
     - Insert into database with:
       - `slug='_orphanage'`
       - `title='Orphaned Pages'`
       - `is_system_page=true`
       - `parent_id=null`
     - Create file: `data/pages/_orphanage.md` (optional, for AI access)
- **Storage**: Stored in both database and file system
  - Database: Regular page record with `is_system_page=true`
  - File System: `data/pages/_orphanage.md` (if needed for AI access)
- **Properties**:
  - Slug: `_orphanage` (reserved, cannot be used by regular pages)
  - Title: "Orphaned Pages"
  - Parent: `null` (top-level)
  - `is_system_page`: `true` (special flag)
  - Never deleted (protected)
  - Not editable by users (system-managed)
- **Protection**:
  - Cannot be deleted (check in delete endpoint)
  - Cannot be edited via UI (system-managed)
  - Can be edited via API with special permissions (future: admin-only endpoint)
- **Identification**: Queries filter by `slug='_orphanage'` or `is_system_page=true`

## API Endpoints

### Get Orphanage
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

### Reassign Orphaned Pages
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

### Clear Orphanage
```
POST /api/orphanage/clear
```

**Request Body:**
```json
{
  "reassign_to": "uuid"  // Optional: reassign all to this parent
}
```

**Permissions:** Admin only

## User Workflow

### When Deleting a Page with Children

1. User attempts to delete page
2. System checks for children
3. If children exist:
   - Show confirmation: "This page has X children. They will be moved to the Orphanage."
   - Options:
     - "Delete and move to Orphanage"
     - "Cancel"
4. After deletion:
   - Notification appears
   - Option to "Reassign Now" or "View Orphanage"
5. If user chooses "Reassign Now":
   - Dialog opens
   - User selects new parent
   - All orphaned pages reassigned
   - Orphanage cleared

### Managing Orphaned Pages

1. Navigate to Orphanage page
2. View all orphaned pages
3. Options:
   - Reassign individual pages
   - Reassign groups (by original parent)
   - Reassign all to same parent
4. Pages removed from orphanage when reassigned

## Benefits

- **Group Management**: Orphaned pages stay together, easier to manage
- **Preservation**: No accidental loss of content
- **Flexibility**: Can reassign immediately or later
- **Organization**: Clear visual indication of orphaned status
- **Bulk Operations**: Reassign multiple pages at once

