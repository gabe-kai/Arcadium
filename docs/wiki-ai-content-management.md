# Wiki AI Content Management

## Quick Reference for AI Agents

**When writing wiki pages, follow these steps:**

1. **Write markdown files** with YAML frontmatter to `services/wiki/data/pages/`
2. **Required frontmatter:**
   - `title`: Page title (required)
   - `slug`: URL-friendly slug (auto-generated from title if omitted)
   - `parent_slug`: Parent page slug (optional, use slug not UUID)
   - `section`: Section name (optional)
   - `order`: Display order (optional, integer)
   - `status`: "published" or "draft" (default: "published")
   - `created_by: "admin"` and `updated_by: "admin"` (always use "admin")
3. **File location:** Mirror hierarchy in filesystem (e.g., `section-name/page.md`)
4. **After writing:**
   - **Option A (Automatic):** If file watcher is running (`python -m app.sync watch`), files sync automatically
   - **Option B (Manual):** Run `python -m app.sync sync-all` to sync to database

**Example:**
```markdown
---
title: "Combat Mechanics"
slug: "combat-mechanics"
parent_slug: "game-mechanics"
section: "game-mechanics"
order: 1
status: "published"
created_by: "admin"
updated_by: "admin"
---

# Combat Mechanics

Content here...
```

**Important Notes:**
- Use `parent_slug` (slug string), not `parent_id` (UUID) - easier for AI to reference
- Always set `created_by: "admin"` and `updated_by: "admin"`
- File paths should mirror the page hierarchy (e.g., `game-mechanics/combat.md`)
- **Custom frontmatter fields are preserved** - You can add any custom fields (e.g., `tags`, `author`, `category`, `ai_generated`) and they will be preserved when users edit pages through the UI
- The sync utility will automatically:
  - Resolve `parent_slug` to `parent_id`
  - Update link tracking
  - Update search index
  - Create version history (on updates)
  - Assign pages to admin user
  - Preserve all frontmatter fields (including custom ones) in the database

---

## What Is This System?

The Wiki AI Content Management System enables AI agents (like Cursor's AI assistant) to create and manage wiki content by writing markdown files directly to the file system. The system automatically synchronizes these files with the database, enabling seamless bidirectional editing workflows between file-based editing (AI/external tools) and browser-based editing (human editors).

### Core Purpose

- **For AI Agents**: Simple file-based content creation without API dependencies
- **For Human Editors**: Browser-based editing with automatic file synchronization
- **For Development**: Hybrid workflows supporting both file and browser editing

## What Does It Do?

The system provides:

1. **File-Based Content Creation**: AI agents write markdown files with YAML frontmatter
2. **Automatic Synchronization**: Files sync to database automatically (file watcher) or manually (CLI commands)
3. **Bidirectional Editing**: Browser edits automatically update files; file edits sync to database
4. **Conflict Resolution**: Grace period protection prevents browser edits from being overwritten
5. **Database Integration**: Automatic metadata extraction, link tracking, search indexing, version history
6. **Admin User Assignment**: AI-created pages automatically assigned to admin user

## How Does It Work?

### Architecture

**File-Based Approach:**
1. AI writes markdown files to `services/wiki/data/pages/` directory
2. Files include YAML frontmatter with metadata (title, slug, section, etc.)
3. Sync utility monitors files and updates database
4. Browser edits automatically write back to files
5. Files and database stay synchronized

**Key Components:**
- **Sync Utility** (`app/sync/sync_utility.py`): Main sync logic
- **File Watcher** (`app/sync/file_watcher.py`): Automatic file monitoring
- **File Scanner** (`app/sync/file_scanner.py`): File system scanning
- **Page Service** (`app/services/page_service.py`): Database ↔ File synchronization
- **File Service** (`app/services/file_service.py`): File operations

**Data Flow:**
```
AI Agent → Markdown File → Sync Utility → Database → Wiki UI
                                        ↕
                                    File Watcher
```

### Sync Process

1. **File Detection**: Scanner finds `.md` files in `data/pages/`
2. **Frontmatter Parsing**: Extract metadata from YAML frontmatter
3. **Content Comparison**: Compare file content hash with database content hash (if enabled)
4. **Conflict Detection**: Compare file modification time vs database `updated_at`, check grace period
5. **Database Update**: Create/update page records with metadata and content
6. **Relationship Resolution**: Resolve `parent_slug` to `parent_id`
7. **Content Processing**: Extract links, update search index, calculate metrics
8. **Version History**: Create version snapshots on updates

### Bidirectional Sync

**File → Database:**
- Content hashes match → Skip sync (content identical, regardless of timestamps)
- Content hashes differ and file modification time > Database `updated_at` → Sync file to database
- Database `updated_at` > File modification time → Skip sync (preserve database)
- Database updated within grace period → Skip sync (protect browser edits)

**Database → File:**
- Page saved in browser → File written immediately with updated content
- Frontmatter regenerated from database metadata
- File modification time updated to match database timestamp

## Features

### Priority 1: Core Features (Critical - All Implemented ✅)

#### Feature 1.1: File-Based Content Creation
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: AI agents write markdown files with YAML frontmatter directly to file system

**Implementation:**
- Location: `services/wiki/data/pages/`
- Format: Markdown with YAML frontmatter
- File structure mirrors page hierarchy
- Custom frontmatter fields preserved

**Requirements:**
- Required fields: `title`, `slug`
- Optional fields: `parent_slug`, `section`, `order`, `status`
- Always use `created_by: "admin"` and `updated_by: "admin"`

#### Feature 1.2: Manual Sync Commands
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: CLI commands to manually sync files to database

**Implementation:**
- `python -m app.sync sync-all`: Sync all files
- `python -m app.sync sync-file <path>`: Sync specific file
- `python -m app.sync sync-dir <dir>`: Sync directory
- `--force` flag: Bypass timestamp checks

**Location**: `app/sync/cli.py`, `app/sync/sync_utility.py`

#### Feature 1.3: Automatic File Watcher
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: File system watcher automatically syncs files when created/modified

**Implementation:**
- Monitors `data/pages/` recursively
- Debouncing (default: 1 second) prevents rapid-fire syncs
- Only watches `.md` files
- Graceful shutdown on Ctrl+C
- Error resilient (continues watching after errors)

**Location**: `app/sync/file_watcher.py`
**Command**: `python -m app.sync watch`

#### Feature 1.4: Database → File Sync
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: Browser edits automatically write files back to file system

**Implementation:**
- `PageService.create_page()` writes file on creation
- `PageService.update_page()` writes file on update
- File path calculated from section/parent hierarchy
- Frontmatter regenerated from database metadata
- Custom frontmatter fields preserved

**Location**: `app/services/page_service.py`, `app/services/file_service.py`

#### Feature 1.5: Frontmatter Parsing and Preservation
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: YAML frontmatter parsed from files and preserved through edits

**Implementation:**
- Frontmatter extracted from file content
- Standard fields (title, slug, section, status, order) managed via UI
- Custom fields (tags, author, etc.) preserved when users edit
- Frontmatter hidden from editor, stored in database
- Full frontmatter stored in `page.content` field

**Location**: `app/utils/markdown_service.py`, `app/services/page_service.py`

#### Feature 1.6: Admin User Assignment
**Priority**: Critical
**Status**: ✅ Implemented
**Description**: AI-created pages automatically assigned to admin user

**Implementation:**
- Sync utility finds or creates admin user
- Pages assigned via `created_by` and `updated_by` fields
- Default admin user ID: `00000000-0000-0000-0000-000000000001`
- Configurable via `SYNC_ADMIN_USER_ID` environment variable

**Location**: `app/sync/sync_utility.py`

### Priority 2: Conflict Resolution (Important - All Implemented ✅)

#### Feature 2.1: Grace Period Conflict Protection
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Protects browser edits from being overwritten by file sync for configurable period

**Implementation:**
- Default grace period: 10 minutes (600 seconds)
- Configurable via `SYNC_CONFLICT_GRACE_PERIOD_SECONDS` environment variable
- Checks time since database `updated_at` before syncing file
- Logs conflict warnings when sync is skipped
- After grace period expires, file edits sync (file takes precedence)

**Location**: `app/sync/sync_utility.py` (`should_sync_file()` method)
**Configuration**: `config.py` (SYNC_CONFLICT_GRACE_PERIOD_SECONDS)

#### Feature 2.2: Timestamp-Based Conflict Detection
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Compares file modification time with database `updated_at` to determine sync necessity

**Implementation:**
- File mtime vs database `updated_at` comparison
- File newer → sync to database (after grace period check)
- Database newer → skip sync (preserve database)
- Prevents unnecessary syncs and data loss

**Location**: `app/sync/sync_utility.py` (`should_sync_file()` method)

#### Feature 2.3: Conflict Logging
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Logs warnings when sync is skipped due to conflicts

**Implementation:**
- Logs when grace period protection triggers
- Includes file path, slug, time since database update
- Helps users understand sync behavior
- Logged via Flask application logger

**Location**: `app/sync/sync_utility.py`

### Priority 3: Database Integration (Important - All Implemented ✅)

#### Feature 3.1: Link Tracking Updates
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Automatically extracts and tracks internal page links

**Implementation:**
- Scans markdown content for internal links
- Updates bidirectional link tracking (forward/backward links)
- Link format: `[text](page-slug)` or `[text](page-slug#anchor)`
- Updates on every sync operation

**Location**: `app/services/link_service.py`, `app/sync/sync_utility.py`

#### Feature 3.2: Search Index Updates
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Updates full-text search index when pages are synced

**Implementation:**
- Indexes page content and metadata
- Full-text search with PostgreSQL
- Keyword extraction
- Updates on every sync operation

**Location**: `app/services/search_index_service.py`, `app/sync/sync_utility.py`

#### Feature 3.3: Version History Creation
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Creates version snapshots when pages are updated

**Implementation:**
- Version created on page updates (not creates)
- Stores content snapshot, metadata, change summary
- Version number increments automatically
- Accessible via API and UI

**Location**: `app/services/version_service.py`, `app/sync/sync_utility.py`

#### Feature 3.4: Parent Slug Resolution
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Converts `parent_slug` (file format) to `parent_id` (database format)

**Implementation:**
- Looks up parent page by slug
- Resolves to UUID for database storage
- Easier for AI agents (use slugs, not UUIDs)
- Handles missing parents gracefully

**Location**: `app/sync/sync_utility.py` (`resolve_parent_slug()` method)

#### Feature 3.5: File Path Calculation
**Priority**: Important
**Status**: ✅ Implemented
**Description**: Calculates file paths based on section and parent hierarchy

**Implementation:**
- Path structure: `{section}/{parent-path}/{slug}.md`
- Recursive parent path calculation
- Updates when page structure changes (section, parent, slug)
- Files moved automatically when paths change

**Location**: `app/services/file_service.py` (`calculate_file_path()` method)

### Priority 4: Workflow Features (Standard - All Implemented ✅)

#### Feature 4.1: Batch Sync Operations
**Priority**: Standard
**Status**: ✅ Implemented
**Description**: Sync multiple files or entire directories at once

**Implementation:**
- `sync-all`: Syncs all files in `data/pages/`
- `sync-dir`: Syncs files in specific directory
- Efficient batch processing
- Statistics reported (created, updated, skipped, errors)

**Location**: `app/sync/sync_utility.py`, `app/sync/cli.py`

#### Feature 4.2: File Deletion Handling
**Priority**: Standard
**Status**: ✅ Implemented
**Description**: Automatically handles orphaned pages when files are deleted

**Implementation:**
- File watcher detects file deletions
- Marks pages as orphaned in database
- Cleanup via orphanage service
- Manual cleanup via `sync-all` if watcher not running

**Location**: `app/sync/file_watcher.py`, `app/sync/sync_utility.py`

#### Feature 4.3: Custom Frontmatter Preservation
**Priority**: Standard
**Status**: ✅ Implemented
**Description**: Preserves custom frontmatter fields through browser edits

**Implementation:**
- Custom fields (tags, author, category, etc.) preserved
- Stored in database `page.content` field
- Not displayed in editor UI
- Round-trips through file → database → file

**Location**: `app/services/page_service.py`, `app/utils/markdown_service.py`

#### Feature 4.4: File Move/Rename Support
**Priority**: Standard
**Status**: ✅ Implemented
**Description**: Automatically moves files when page structure changes (slug, section, parent)

**Implementation:**
- Detects file path changes
- Moves file to new location
- Updates file content with new metadata
- Cleans up old empty directories

**Location**: `app/services/page_service.py`, `app/services/file_service.py`

### Priority 5: Future Enhancements

#### Feature 5.1: Content Comparison for Sync Decisions
**Priority**: Low (Nice to Have)
**Status**: ✅ Implemented
**Description**: Compare actual file content with database content using hash comparison, not just timestamps

**Implementation:**
- SHA256 hash comparison of file content vs database content
- Skips sync when content hashes match, even if timestamps differ
- Prevents unnecessary syncs when content is identical
- Configurable via `SYNC_ENABLE_CONTENT_COMPARISON` (default: True)
- Content comparison runs before timestamp/grace period checks for efficiency

**Location**: `app/sync/sync_utility.py` (`should_sync_file()`, `_compute_content_hash()`, `_get_file_content_hash()`)
**Configuration**: `config.py` (SYNC_ENABLE_CONTENT_COMPARISON)

**Behavior:**
- If content hashes match → Skip sync (content identical)
- If content hashes differ → Continue with timestamp and grace period checks
- Falls back to timestamp-based logic if content comparison fails or is disabled

#### Feature 5.2: Enhanced Conflict Warnings in UI
**Priority**: Low (Nice to Have)
**Status**: ✅ Implemented
**Description**: Display conflict warnings in browser UI when file sync conflicts are detected

**Implementation:**
- Conflict detection when loading pages for editing (GET endpoint)
- Conflict information included in API responses (GET and PUT endpoints)
- Visual warning banner displayed in EditPage component
- Shows conflict message, file modification time, and grace period status
- Only displayed for users who can edit the page

**Location**:
- Backend: `app/services/page_service.py` (`check_sync_conflict()`), `app/routes/page_routes.py`
- Frontend: `client/src/components/common/SyncConflictWarning.jsx`, `client/src/pages/EditPage.jsx`

**Behavior:**
- Warning appears when file is newer than database or content differs
- Displays human-readable conflict message
- Shows remaining grace period protection time (if applicable)
- Warning persists until conflict is resolved or grace period expires

#### Feature 5.3: Three-Way Merge Capabilities
**Priority**: Low (Nice to Have)
**Status**: ✅ Partially Implemented (Merge Utility Ready)
**Description**: Merge utility available for automatically merging conflicting edits from file and database

**Implementation:**
- Merge utility implemented (`app/sync/merge_utility.py`)
- Two-way merge strategy using Python's `difflib.SequenceMatcher`
- Automatically merges non-conflicting changes
- Marks conflicts with Git-style conflict markers (`<<<<<<< FILE`, `=======`, `>>>>>>> DATABASE`)
- Returns merged content with conflict count

**Location**: `app/sync/merge_utility.py` (`MergeUtility.merge()`)

**Current Behavior**:
- Merge utility is available but not yet integrated into the sync process
- File sync currently takes precedence after grace period expires
- Merge utility can be called programmatically when needed

**Usage:**
```python
from app.sync.merge_utility import MergeUtility

merged_content, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)
```

**Future Enhancement**: Integrate merge utility into sync process to automatically attempt merges when conflicts are detected (after grace period).

#### Feature 5.4: Sync Status Tracking
**Priority**: Low (Nice to Have)
**Status**: ✅ Implemented
**Description**: Track which source (file/database) was last updated for each page

**Implementation:**
- Sync status information computed on-the-fly by comparing file and database timestamps
- Included in API responses (GET and PUT page endpoints)
- Provides information about which source was last updated and whether they're in sync

**Location**: `app/services/page_service.py` (`get_sync_status()`), `app/routes/page_routes.py`

**Response Fields:**
- `last_updated_source`: "file", "database", or "synced"
- `file_modification_time`: Unix timestamp of file modification
- `database_updated_at`: Unix timestamp of database update
- `is_synced`: Boolean indicating if file and database are in sync (within 1 second)
- `time_difference_seconds`: Time difference between file and database timestamps

**Behavior:**
- Status computed by comparing file modification time with database `updated_at`
- Considered "synced" if timestamps are within 1 second of each other
- Only included in API responses for users who can edit the page
- Available for all pages with a file_path


## Implementation Details

### File Format

**Structure:**
```markdown
---
title: "Page Title"
slug: "page-slug"
parent_slug: "parent-slug"  # Optional
section: "section-name"     # Optional
order: 1                    # Optional
status: "published"         # Optional, default: "published"
created_by: "admin"         # Required
updated_by: "admin"         # Required
# Custom fields preserved:
tags: [ai, content]
author: "AI Assistant"
---

# Page Title

Markdown content here...
```

**Rules:**
- Use `parent_slug` (slug string), not `parent_id` (UUID)
- Always set `created_by: "admin"` and `updated_by: "admin"`
- File paths mirror hierarchy: `{section}/{parent-path}/{slug}.md`
- Custom frontmatter fields preserved through edits

### Sync Utility Structure

```
services/wiki/
  app/
    sync/
      __init__.py
      cli.py                 # CLI commands
      sync_utility.py        # Main sync logic
      file_scanner.py        # Find and scan files
      file_watcher.py        # File system watcher
    services/
      page_service.py        # Page CRUD with file sync
      file_service.py        # File operations
      link_service.py        # Link tracking
      search_index_service.py # Search indexing
      version_service.py     # Version history
    utils/
      markdown_service.py    # Frontmatter parsing
```

### Configuration

**Environment Variables:**
- `SYNC_CONFLICT_GRACE_PERIOD_SECONDS`: Grace period for conflict protection (default: 600)
- `SYNC_ENABLE_CONTENT_COMPARISON`: Enable content hash comparison (default: true)
- `SYNC_ADMIN_USER_ID`: Admin user UUID for sync operations
- `WIKI_PAGES_DIR`: Directory for page files (default: `data/pages`)

### Error Handling

**Common Errors:**
- **Invalid frontmatter**: Log error, skip file
- **Missing parent**: Log warning, set parent to null
- **Duplicate slug**: Log error, append number to slug
- **Invalid markdown**: Log warning, save anyway
- **File not found**: Error if file_path doesn't exist
- **Permission errors**: File write failures

**Validation:**
- YAML frontmatter format (must be valid YAML)
- Slug format (URL-safe, alphanumeric with hyphens)
- Markdown syntax (basic validation)
- Circular parent references (prevents infinite loops)

## Usage Examples

### Example 1: AI Creates Page

```bash
# 1. AI writes file
cat > services/wiki/data/pages/mechanics/combat.md << 'EOF'
---
title: "Combat System"
slug: "combat"
section: "mechanics"
status: "published"
created_by: "admin"
updated_by: "admin"
---

# Combat System

Combat mechanics description...
EOF

# 2. Sync (if watcher not running)
python -m app.sync sync-file data/pages/mechanics/combat.md
```

### Example 2: File Watcher Workflow

```bash
# Terminal 1: Start watcher
cd services/wiki
python -m app.sync watch

# Terminal 2: AI writes files
# Files automatically sync as they're written
```

### Example 3: Browser Edit Workflow

1. User edits page in browser editor
2. Saves changes
3. File automatically updates with new content
4. Future file edits respect grace period

## Troubleshooting

### Common Issues

**File not syncing to database:**
- Check if content hashes match (content comparison may skip sync if content is identical)
- Check file modification time is newer than database `updated_at`
- Verify file watcher is running (if using automatic sync)
- Check if page was recently edited in browser (grace period protection)
- Check server logs for sync errors or conflict warnings
- Use `--force` flag to bypass content/timestamp checks (use with caution)

**Database changes not appearing in file:**
- File should update immediately when page is saved in browser
- Check server logs for file write errors
- Verify file permissions
- Ensure page has a valid `file_path` in database

**Duplicate pages after rename:**
- Ensure file watcher is running or run manual sync after renaming
- Old file with old slug should be moved/updated automatically
- Check both old and new file paths don't exist simultaneously

**Sync conflicts:**
- Check server logs for conflict warnings
- Understand grace period behavior
- Identify which source (file/database) has desired content
- Wait for grace period to expire, or manually resolve conflicts
- Use `--force` sync only when you understand the consequences

### Debugging

**Enable detailed logging:**
- Check Flask application logs for sync operations
- File watcher outputs sync status to console
- Look for conflict warnings in logs

**Verify file and database state:**
- Compare file modification time with database `updated_at`
- Check file content matches expected state
- Verify database page content and metadata

## Status Summary

**Overall Status**: ✅ **Production Ready**

- ✅ All Priority 1 (Critical) features implemented
- ✅ All Priority 2 (Important) features implemented
- ✅ All Priority 3 (Important) features implemented
- ✅ All Priority 4 (Standard) features implemented
- ❌ Priority 5 (Future Enhancements) not implemented

**Production Readiness**: The system is fully functional and ready for use. Future enhancements are optional improvements, not blockers.
