# Wiki AI Content Management

## Overview

This document describes how AI agents (like Cursor's AI assistant) can write and update wiki pages, ensuring proper integration with the wiki system while maintaining database consistency.

## Requirements

- AI-written pages should be assigned to admin user
- All admin users can manually edit AI-written pages
- Method should be simple and reliable for AI agents
- Must maintain database consistency (metadata, links, versions, search index)

## Recommended Approach: Direct File Writing + Sync Utility

### Why This Approach?

**Advantages:**
- ✅ Simplest for AI agents (just write files)
- ✅ No authentication needed
- ✅ No network dependencies
- ✅ Fast and reliable
- ✅ Works even if wiki service is down
- ✅ Easy to batch write multiple pages

**How It Works:**
1. AI writes markdown files directly to `services/wiki/data/pages/`
2. Files include YAML frontmatter with metadata
3. Wiki service includes a sync utility that:
   - Scans for new/changed files
   - Updates database metadata
   - Creates version history entries
   - Updates link tracking
   - Updates search index
4. Sync can run automatically (file watcher) or manually (CLI command)

## File Format for AI Writing

### Standard Markdown with YAML Frontmatter

```markdown
---
title: "Page Title"
slug: "page-slug"
parent_slug: "parent-page-slug"  # Optional: use slug instead of ID
section: "section-name"
order: 1
status: "published"
created_by: "admin"  # Special value: assigns to admin user
updated_by: "admin"
---

# Page Title

Page content in markdown...
```

### AI Writing Rules

1. **Slug Generation**: Auto-generate from title if not specified
2. **Parent Reference**: Use `parent_slug` (easier than UUID for AI)
3. **Admin Assignment**: Always use `created_by: "admin"` and `updated_by: "admin"`
4. **File Location**: Mirror hierarchy in file system
5. **YAML Frontmatter**: Always include required fields

## Sync Utility

### CLI Command

```bash
# Sync all files (new and changed)
python -m app.sync sync-all

# Sync specific file
python -m app.sync sync-file data/pages/section/page.md

# Sync directory
python -m app.sync sync-dir data/pages/section/

# Watch mode (auto-sync on file changes)
python -m app.sync watch
```

### Sync Process

1. **Scan Files**: Find all `.md` files in `data/pages/`
2. **Parse Frontmatter**: Extract metadata from YAML
3. **Check Database**: Compare file modification time with database `updated_at`
4. **Create/Update Pages**:
   - If page doesn't exist: Create new page record
   - If file is newer: Update page record
   - Create version history entry
5. **Update Relationships**:
   - Resolve `parent_slug` to `parent_id`
   - Update section if changed
6. **Process Content**:
   - Extract links and update link tracking
   - Update search index (full-text and keywords)
   - Calculate page size and word count
   - Generate TOC data
7. **Admin User Assignment**:
   - Find or create "admin" system user
   - Assign `created_by` and `updated_by` to admin user

### File Watcher (Optional)

- Watch `data/pages/` directory for changes
- Auto-sync when files are created/modified
- Debounce rapid changes
- Log sync operations

## Alternative: AI Write API Endpoint

### Simpler API for AI Agents

If direct file writing is not preferred, provide a simplified API endpoint:

```
POST /api/ai/write-page
```

**Request:**
```json
{
  "title": "Page Title",
  "slug": "page-slug",
  "content": "# Markdown content...",
  "parent_slug": "parent-slug",
  "section": "section-name",
  "order": 1
}
```

**Features:**
- No authentication required (or simple token)
- Auto-assigns to admin user
- Handles all database updates automatically
- Returns page ID for reference

**Advantages:**
- Ensures immediate database consistency
- No sync step needed
- Can validate content before saving

**Disadvantages:**
- Requires wiki service to be running
- Requires network/API call
- More complex for AI agent

## Implementation Details

### Sync Utility Structure

```
services/wiki/
  app/
    sync/
      __init__.py
      sync_utility.py      # Main sync logic
      file_scanner.py       # Find and scan files
      frontmatter_parser.py # Parse YAML frontmatter
      db_sync.py            # Database operations
      link_updater.py       # Update link tracking
      index_updater.py      # Update search index
```

### Admin User Handling

```python
# Find first admin user (first registered user becomes admin)
# If no admin exists, create system admin user
admin_user = User.query.filter_by(role='admin').first()
if not admin_user:
    # Create system admin user for AI content
    admin_user = User(
        username='system-admin',
        email='system@arcadium',
        role='admin',
        is_system_user=True,
        is_first_user=False  # Not the first user, but system-created
    )
    db.session.add(admin_user)
    db.session.commit()
```

### Parent Reference Format

#### In File System (YAML Frontmatter)
- Use `parent_slug`: `parent_slug: "parent-page-slug"`
- Easier for AI to reference by slug than UUID

#### In API
- Use `parent_id`: `parent_id: "uuid"`
- More reliable (UUIDs don't change, slugs can)

#### Conversion
- Sync utility converts `parent_slug` → `parent_id` when syncing files
- API can optionally accept `parent_slug` and resolve to `parent_id` (future enhancement)

### Parent Slug Resolution

```python
def resolve_parent_slug(parent_slug):
    if not parent_slug:
        return None
    parent = Page.query.filter_by(slug=parent_slug).first()
    if not parent:
        # Log warning, create placeholder, or skip
        return None
    return parent.id
```

## AI Writing Workflow

### Recommended Workflow

1. **User directs AI in Cursor**: "Create a page about combat mechanics"
2. **AI writes markdown file**:
   ```bash
   # AI creates file
   services/wiki/data/pages/game-mechanics/combat-mechanics.md
   ```
3. **AI includes proper frontmatter**:
   ```yaml
   ---
   title: "Combat Mechanics"
   slug: "combat-mechanics"
   parent_slug: "game-mechanics"
   section: "game-mechanics"
   order: 1
   created_by: "admin"
   updated_by: "admin"
   ---
   ```
4. **User runs sync** (or auto-sync triggers):
   ```bash
   python -m app.sync sync-file data/pages/game-mechanics/combat-mechanics.md
   ```
5. **Wiki service updates database**:
   - Creates page record
   - Assigns to admin user
   - Updates links and index
   - Creates version history

### Batch Writing

AI can write multiple files at once, then sync all:

```bash
# AI writes multiple files
# Then sync all
python -m app.sync sync-all
```

## File System Structure

### Directory Organization

```
services/wiki/data/pages/
  introduction/
    getting-started.md
    overview.md
  game-mechanics/
    combat/
      basic-combat.md
      advanced-combat.md
    economy/
      trading.md
```

### File Naming

- Use slug as filename: `{slug}.md`
- Mirror hierarchy in directory structure
- Parent directories represent sections/parents

## Error Handling

### Sync Errors

- **Invalid frontmatter**: Log error, skip file
- **Missing parent**: Log warning, set parent to null
- **Duplicate slug**: Log error, append number to slug
- **Invalid markdown**: Log warning, save anyway (user can fix)

### Validation

- Validate YAML frontmatter format
- Validate slug format (URL-safe)
- Validate markdown syntax (basic)
- Check for circular parent references

## Recommendations

### For AI Agents

**Use direct file writing** because:
1. Simplest and most reliable
2. No dependencies on service being running
3. Easy to batch write multiple pages
4. Files are human-readable and editable
5. Can be version controlled in git

### Sync Strategy

**Use manual sync** (user-triggered) because:
1. More predictable
2. User can review before syncing
3. Can batch multiple changes
4. Avoids race conditions

**Optional auto-sync** for:
- Development/testing
- Automated workflows
- Real-time updates (if needed)

## Example: AI Writing a Page

### Step 1: AI Creates File

```markdown
---
title: "Character Creation"
slug: "character-creation"
parent_slug: "game-mechanics"
section: "game-mechanics"
order: 2
created_by: "admin"
updated_by: "admin"
---

# Character Creation

This page describes how players create characters...

## Attributes

Characters have the following attributes...

## Classes

Players can choose from several classes...
```

### Step 2: Save to File System

```python
# AI writes file
file_path = "services/wiki/data/pages/game-mechanics/character-creation.md"
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(markdown_content)
```

### Step 3: User Syncs

```bash
cd services/wiki
python -m app.sync sync-file data/pages/game-mechanics/character-creation.md
```

### Step 4: Database Updated

- Page record created
- Assigned to admin user
- Links extracted and tracked
- Search index updated
- Version history created

## Integration with Cursor

### Cursor AI Workflow

1. User: "Create a wiki page about magic system"
2. AI: Writes markdown file with proper frontmatter
3. AI: Saves to `services/wiki/data/pages/game-mechanics/magic-system.md`
4. User: Runs sync command or triggers auto-sync
5. Wiki: Page appears in wiki with all features working

### Cursor Commands

Add to Makefile or scripts:

```makefile
wiki-sync:
	cd services/wiki && python -m app.sync sync-all

wiki-sync-file:
	cd services/wiki && python -m app.sync sync-file $(FILE)
```

## Summary

**Recommended Method**: Direct file writing + sync utility

**Why**: Simplest for AI, most reliable, no dependencies

**Implementation**: 
- AI writes markdown files with YAML frontmatter
- Sync utility updates database
- Admin user assignment automatic
- All wiki features work normally

