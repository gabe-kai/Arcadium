# Wiki Service Architecture

## Overview

The Wiki Service uses a hybrid storage approach: Markdown files for content (enabling AI access) and PostgreSQL database for metadata, relationships, and search capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/REST API
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Wiki Service (Flask)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │  Services   │  │   Models     │      │
│  │  (Handlers)  │─▶│  (Business  │─▶│  (Database   │      │
│  │              │  │   Logic)    │  │   ORM)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  File System     │      │   PostgreSQL     │
    │  (Markdown)      │      │   (Metadata)     │
    │                  │      │                  │
    │  pages/          │      │  - pages         │
    │    section/      │      │  - comments      │
    │      page.md     │      │  - links         │
    │                  │      │  - index         │
    └──────────────────┘      └──────────────────┘
```

## Storage Strategy

### File System (Content)
- **Location**: `services/wiki/data/pages/`
- **Format**: Markdown files with YAML frontmatter
- **Structure**: Mirrors page hierarchy
  ```
  data/pages/
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

#### File Path Calculation
1. **Base Path**: `services/wiki/data/pages/`
2. **Section Directory**: If section exists, add `{section}/`
3. **Parent Hierarchy**: If parent exists, add parent's directory path
4. **Filename**: `{slug}.md`

**Example:**
- Page: slug="combat", section="game-mechanics", parent="game-mechanics" (slug)
- File path: `data/pages/game-mechanics/combat.md`

**When Page Moves:**
- File is moved to new location
- `file_path` field updated in database
- Old file deleted (or archived)

### Database (Metadata & Relationships)
- **Tables**:
  - `pages` - Page metadata, relationships, ordering
  - `comments` - User comments and recommendations
  - `page_links` - Link relationships between pages
  - `index_entries` - Search index
  - `page_versions` - Version history (optional)

## Data Flow

### Reading a Page
1. Client requests page via API
2. Service queries database for page metadata
3. Service reads Markdown file from filesystem
4. Service parses Markdown to HTML
5. Service extracts headings for TOC
6. Service queries database for:
   - Forward links (pages this page links to)
   - Backlinks (pages that link here)
   - Comments
7. Service combines all data and returns JSON response

### Creating/Updating a Page
1. Client sends page data via API
2. Service validates permissions (Writer/Admin)
3. Service creates version snapshot (current content → version history) if updating
4. Service saves Markdown file to filesystem (with YAML frontmatter)
5. Service calculates page size (KB) and word count (images excluded)
6. Service updates database metadata
7. Service scans content for internal links (format: `[text](page-slug)` or `[text](page-slug#anchor)`)
8. Service updates link tracking tables (bidirectional)
9. Service updates search index:
   - Full-text: Index all content via PostgreSQL
   - Keywords: Auto-extract via NLP + manual tags
   - Indexing happens synchronously on save
10. Service generates TOC from headings (H2-H6, anchor = slug from heading text)
11. Service calculates diff for version history
12. Service returns updated page data

### Link Tracking
- **On Save**: Parse Markdown for internal links
  - Format: `[text](page-slug)` or `[text](page-slug#anchor)` or `[text](/wiki/pages/page-slug)`
  - Extract slug (before `#` if anchor present)
  - Store link text and target slug
- **Supported Link Formats**:
  - Internal: `[text](page-slug)`, `[text](page-slug#anchor)`, `[text](/wiki/pages/page-slug)`
  - External: `[text](https://example.com)` - Not tracked in link database
- **Link Parsing Rules**:
  - Extract text between `[` and `]` (link text)
  - Extract URL between `(` and `)` (link target)
  - If target starts with `http://` or `https://`: External link (not tracked)
  - If target is relative or starts with `/`: Internal link
  - Extract slug (before `#` if anchor present)
  - Validate slug exists in database
  - Create `page_links` entry
- **Update Links Table**: Create/update `page_links` entries
- **Update Backlinks**: Automatically maintain bidirectional relationships
- **Link Validation**: Check that linked pages exist (warn if not found, but don't block save)
- **Link Updates**: When page slug changes, update all links pointing to it

## Component Structure

### Routes (`app/routes/`)
- `wiki_routes.py` - Page CRUD endpoints
- `comment_routes.py` - Comment management
- `search_routes.py` - Search and indexing
- `navigation_routes.py` - Hierarchy and navigation
- `upload_routes.py` - File uploads
- `orphanage_routes.py` - Orphaned page management
- `extraction_routes.py` - Section extraction endpoints
- `admin_routes.py` - Admin dashboard and configuration

### Services (`app/services/`)
- `page_service.py` - Page business logic
- `file_service.py` - File system operations
- `markdown_service.py` - Markdown parsing and rendering
- `link_service.py` - Link tracking and validation
- `index_service.py` - Search indexing (full-text and keyword extraction)
- `toc_service.py` - Table of contents generation
- `permission_service.py` - Role-based access control
- `version_service.py` - Version history and diff management
- `orphanage_service.py` - Orphanage system management
- `extraction_service.py` - Section extraction logic
- `admin_service.py` - Admin dashboard and configuration
- `notification_service.py` - Internal messaging for oversized pages
- `size_monitoring_service.py` - Page size calculation and monitoring

### Models (`app/models/`)
- `page.py` - Page database model
- `comment.py` - Comment model
- `page_link.py` - Link relationship model
- `index_entry.py` - Search index model (full-text and keywords)
- `page_version.py` - Version history model
- `user.py` - User model (references Auth Service)
- `wiki_config.py` - System configuration model
- `oversized_page_notification.py` - Oversized page tracking
- `image.py` - Image metadata model
- `page_image.py` - Image-page association model

### Utils (`app/utils/`)
- `markdown_parser.py` - Markdown to HTML conversion
- `link_extractor.py` - Extract links from Markdown
- `slug_generator.py` - Generate URL-friendly slugs (auto-generate, validate uniqueness)
- `file_manager.py` - File system utilities
- `section_extractor.py` - Extract sections from pages
- `size_calculator.py` - Calculate page size and word count
- `keyword_extractor.py` - Automatic keyword extraction (NLP)

### Sync Utility (`app/sync/`)
- `sync_utility.py` - Main sync logic for AI-written files
- `file_scanner.py` - Find and scan markdown files
- `frontmatter_parser.py` - Parse YAML frontmatter
- `db_sync.py` - Database synchronization
- `link_updater.py` - Update link tracking from files
- `index_updater.py` - Update search index from files

## Database Schema

### Pages Table
```sql
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- Calculated from section/parent hierarchy
    parent_id UUID REFERENCES pages(id),
    section VARCHAR(100),  -- Organizational grouping (independent of parent)
    order_index INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'published',  -- 'draft' or 'published'
    is_public BOOLEAN DEFAULT TRUE,
    word_count INTEGER DEFAULT 0,
    content_size_kb FLOAT DEFAULT 0,
    is_orphaned BOOLEAN DEFAULT FALSE,
    orphaned_from UUID REFERENCES pages(id),
    is_system_page BOOLEAN DEFAULT FALSE,  -- TRUE for system pages like orphanage
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_pages_parent ON pages(parent_id);
CREATE INDEX idx_pages_section ON pages(section);
CREATE INDEX idx_pages_slug ON pages(slug);
CREATE INDEX idx_pages_orphaned ON pages(is_orphaned) WHERE is_orphaned = TRUE;
CREATE INDEX idx_pages_status ON pages(status);
CREATE INDEX idx_pages_system ON pages(is_system_page) WHERE is_system_page = TRUE;
```

### Wiki Config Table
```sql
CREATE TABLE wiki_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID NOT NULL
);

INSERT INTO wiki_config (key, value, updated_by) VALUES
    ('max_file_upload_size_mb', '10', 'system'),
    ('max_page_size_kb', NULL, 'system');
```

### Oversized Page Notifications Table
```sql
CREATE TABLE oversized_page_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    current_size_kb FLOAT NOT NULL,
    max_size_kb FLOAT NOT NULL,
    resolution_due_date TIMESTAMP NOT NULL,
    notified_users UUID[] NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX idx_oversized_page ON oversized_page_notifications(page_id);
CREATE INDEX idx_oversized_resolved ON oversized_page_notifications(resolved);
CREATE INDEX idx_oversized_due_date ON oversized_page_notifications(resolution_due_date);
```

### Comments Table
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES comments(id),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    is_recommendation BOOLEAN DEFAULT FALSE,
    thread_depth INTEGER DEFAULT 1,  -- Calculated depth in thread (1 = top level)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comments_page ON comments(page_id);
CREATE INDEX idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX idx_comments_depth ON comments(thread_depth);
```

**Note:** `thread_depth` is calculated and stored when comment is created. Maximum depth is 5.

### Page Links Table
```sql
CREATE TABLE page_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    to_page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    link_text VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_page_id, to_page_id)
);

CREATE INDEX idx_links_from ON page_links(from_page_id);
CREATE INDEX idx_links_to ON page_links(to_page_id);
```

### Index Entries Table
```sql
CREATE TABLE index_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    term VARCHAR(255) NOT NULL,
    context TEXT,
    position INTEGER,
    is_keyword BOOLEAN DEFAULT FALSE, -- TRUE for extracted keywords, FALSE for full-text
    is_manual BOOLEAN DEFAULT FALSE, -- TRUE if manually tagged, FALSE if auto-extracted
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_index_term ON index_entries(term);
CREATE INDEX idx_index_page ON index_entries(page_id);
CREATE INDEX idx_index_keyword ON index_entries(is_keyword) WHERE is_keyword = TRUE;
CREATE INDEX idx_index_manual ON index_entries(is_manual) WHERE is_manual = TRUE;
```

### Page Versions Table
```sql
CREATE TABLE page_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL, -- Full markdown content at this version
    changed_by UUID NOT NULL,
    change_summary TEXT,
    diff_data JSONB, -- Stores diff information for comparison
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(page_id, version)
);

CREATE INDEX idx_versions_page ON page_versions(page_id);
CREATE INDEX idx_versions_version ON page_versions(page_id, version DESC);
```

### Images Table
```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uuid VARCHAR(255) UNIQUE NOT NULL,  -- UUID used in filename
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes INTEGER,
    uploaded_by UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE page_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(page_id, image_id)
);

CREATE INDEX idx_images_uuid ON images(uuid);
CREATE INDEX idx_page_images_page ON page_images(page_id);
CREATE INDEX idx_page_images_image ON page_images(image_id);
```

**Image Storage Strategy:**
- **File System**: Images stored as `{uuid}.{ext}` in `data/uploads/images/`
- **Database**: Image metadata stored in `images` table
- **Association**: Image-page association via `page_images` junction table
- **Metadata JSON Files**: Optional JSON files in `data/uploads/images/metadata/` for AI access (contains original filename, page associations, upload date)

## Security Considerations

### File System Security
- Validate file paths to prevent directory traversal
- Sanitize filenames/slugs
- Limit file size for uploads
- Validate Markdown content before saving

### Permission Checks
- Middleware for role-based access control
- Verify ownership before allowing edits/deletes
- Admin override for deletions
- Rate limiting on comment creation

### Data Validation
- Validate Markdown syntax
- Sanitize HTML output (prevent XSS)
- Validate link targets exist
- Check for circular page references

## Performance Optimizations

### Caching
- Cache rendered HTML for frequently accessed pages
- Cache TOC generation
- Cache navigation tree
- Use Redis for session and cache (future)

### Lazy Loading
- Load comments on demand
- Paginate comment lists
- Lazy-load child pages in navigation tree

### Search Indexing
- **When Indexing Happens**: Synchronous indexing immediately on page save (no background jobs)
- **Failure Handling**: If indexing fails, page save still succeeds (index updated on next save)
- **Incremental Updates**: Only re-index changed pages (delete old entries, create new ones)

#### Full-Text Indexing
- Strip markdown formatting
- Extract plain text
- Index via PostgreSQL full-text search (`ts_vector`, `ts_query`)
- Store in `index_entries` with `is_keyword=false`
- Relevance ranking via PostgreSQL `ts_rank` (no custom weighting)

#### Keyword Extraction
- **Automatic Extraction (NLP)**:
  - Method: TF-IDF (Term Frequency-Inverse Document Frequency)
  - Library: NLTK or spaCy (Python)
  - Process:
    1. Extract text from markdown (strip formatting)
    2. Tokenize and remove stop words
    3. Calculate TF-IDF scores
    4. Top 10-15 terms become keywords
  - Storage: `index_entries` with `is_keyword=true`, `is_manual=false`
- **Manual Tagging**:
  - UI: Keyword editor in page metadata section
  - Process: Writer adds/removes keywords manually
  - Storage: `index_entries` with `is_keyword=true`, `is_manual=true`
  - Priority: Manual keywords take precedence (can override auto-extracted)

#### Search Query
- Uses PostgreSQL `ts_vector` and `ts_query` for full-text search
- Relevance ranking via PostgreSQL `ts_rank`
- No custom weighting (pure PostgreSQL relevance)
- Consider Elasticsearch for advanced search (future)

### File Operations
- Async file I/O where possible
- Batch file operations
- Monitor file system performance

## Integration Points

### Auth Service
- JWT token validation
- User role retrieval
- User profile information

### Shared Code
- Use shared auth utilities for token validation
- Use shared logging utilities
- Use shared error handling

## Deployment Considerations

### File Storage
- Ensure `data/pages/` directory is writable
- Backup strategy for file system
- Consider cloud storage for production (S3, etc.)

### Database
- Regular backups
- Migration strategy
- Connection pooling

### Scaling
- Stateless service design (files can be on shared storage)
- Load balancer ready
- Consider CDN for static assets

