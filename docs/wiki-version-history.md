# Wiki Version History System

## Overview

The wiki service maintains a complete version history for every page, allowing users to view changes, compare versions, and rollback to previous versions.

## Version Storage

### Database Storage
- Each version is stored in the `page_versions` table
- Full content is stored (not just diffs) for easy retrieval
- Diff data is calculated and stored for efficient comparison

### File System
- Current version is always in the Markdown file
- Previous versions are stored in database only
- File system contains only the latest version

## Version Creation

### Automatic Versioning
- Every page edit creates a new version
- Version number increments automatically
- Version includes:
  - Full markdown content
  - Title at time of edit
  - User who made the change
  - Timestamp
  - Optional change summary
  - Diff data (JSON format)

### Version Metadata
```json
{
  "version": 5,
  "title": "Page Title",
  "changed_by": "user-id",
  "change_summary": "Updated combat mechanics section",
  "created_at": "2024-01-15T10:30:00Z",
  "diff_data": {
    "additions": 150,
    "deletions": 45,
    "changed_sections": ["combat", "mechanics"]
  }
}
```

## Version Comparison

### Diff Display Options

#### Inline Diff (Default)
- Shows additions in green
- Shows deletions in red (strikethrough)
- Context lines around changes
- Side-by-side word-level comparison

#### Side-by-Side Comparison
- Left: Previous version
- Right: Current version
- Highlighted differences
- Scroll synchronization

### Diff Calculation
- Uses text diff algorithm (e.g., Myers diff)
- Tracks:
  - Character-level changes
  - Line-level changes
  - Section-level changes
- Stores diff in JSON format for efficient rendering

## Version History UI

### History View
- Chronological list of all versions
- Shows:
  - Version number
  - Date and time
  - User who made change
  - Change summary (if provided)
  - Diff statistics (lines added/removed)
- Click to view version
- Compare any two versions

### Version Viewer
- Display full content of selected version
- Option to compare with current or another version
- "Restore this version" button (for admins/writers)

## Rollback Functionality

### Who Can Rollback
- **Writers**: Can rollback pages they created
- **Admins**: Can rollback any page

### Rollback Process
1. User selects version to restore
2. System creates new version (current becomes history)
3. Content is restored from selected version
4. File system is updated
5. New version is created with note: "Restored from version X"

### Rollback Safety
- Cannot delete versions (only create new ones)
- Full audit trail maintained
- Rollback itself creates a version entry

## Version Retention

### Retention Policy
- **Keep all versions indefinitely** (no deletion or archiving)
- All versions stored in database
- Full audit trail maintained
- No storage limits (all versions kept)

### Storage Considerations
- Monitor database size as versions accumulate
- Consider compression for very old versions (future optimization)
- Maintain index for quick access
- Regular backups include all version history

## Change Summaries

### Optional Change Summary
- Writers can provide a summary when saving
- Helps identify significant changes
- Shown in version history list
- Auto-generated summary if not provided (e.g., "Minor edits")

### Auto-Generated Summaries
- Based on diff analysis:
  - "Major rewrite" (if >50% changed)
  - "Minor edits" (if <10% changed)
  - "Section updated: [section name]"
  - "Added new section: [section name]"

## API Endpoints

### Get Version History
```
GET /api/pages/{page_id}/versions
```

**Response:**
```json
{
  "versions": [
    {
      "version": 5,
      "title": "Page Title",
      "changed_by": {
        "id": "user-id",
        "username": "writer"
      },
      "change_summary": "Updated combat section",
      "created_at": "2024-01-15T10:30:00Z",
      "diff_stats": {
        "additions": 150,
        "deletions": 45
      }
    }
  ]
}
```

### Get Specific Version
```
GET /api/pages/{page_id}/versions/{version}
```

**Response:**
```json
{
  "version": 5,
  "title": "Page Title",
  "content": "# Full markdown content...",
  "html_content": "<h1>Full HTML content...</h1>",
  "changed_by": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Compare Versions
```
GET /api/pages/{page_id}/versions/compare?from={version1}&to={version2}
```

**Response:**
```json
{
  "from_version": 3,
  "to_version": 5,
  "diff": {
    "additions": 150,
    "deletions": 45,
    "changes": [
      {
        "type": "addition",
        "line": 10,
        "content": "New content here"
      },
      {
        "type": "deletion",
        "line": 15,
        "content": "Old content removed"
      }
    ]
  }
}
```

### Restore Version
```
POST /api/pages/{page_id}/versions/{version}/restore
```

**Response:**
```json
{
  "message": "Version restored successfully",
  "new_version": 6,
  "page": {...}
}
```

## Implementation Notes

### Diff Algorithm
- Use library like `difflib` (Python) or `diff-match-patch`
- Calculate diff on save
- Store diff in JSON format
- Render diff on client side for performance

### Performance Considerations
- Lazy-load version content (only load when viewed)
- Cache diff calculations
- Paginate version history list
- Index version queries by page_id and version

### Security
- Track who restored which version
- Prevent version tampering
- Maintain immutable version history
- Audit log for all version operations
