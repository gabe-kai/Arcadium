# Wiki Service Specification

## Overview

The Wiki Service is a comprehensive documentation and planning system for the Arcadium game project. It provides a book-like reading experience with hierarchical organization, role-based access control, and collaborative editing capabilities.

## Core Requirements

### Storage Format

- **Local File Storage**: Pages are stored as local files to enable AI access and updates
- **Format**: Markdown files with YAML frontmatter for metadata
- **Structure**: File system mirrors page hierarchy (folders for sections, files for pages)
- **Location**: `services/wiki/data/pages/` directory

### User Roles and Permissions

#### Viewer (Unregistered)
- ✅ View all public pages
- ❌ Cannot comment, edit, or create

#### Player (Registered)
- ✅ View all pages
- ✅ Leave comments on pages
- ✅ Recommend updates/suggestions
- ❌ Cannot edit or create pages

#### Writer
- ✅ All Player permissions
- ✅ Edit existing pages
- ✅ Create new pages
- ✅ Create new sections
- ✅ Save pages as drafts
- ✅ Extract sections to new pages
- ✅ Promote sections to child/sibling pages
- ❌ Cannot delete pages (except own)

#### Admin
- ✅ All Writer permissions
- ✅ Delete any page (including those written by others)
- ✅ Manage user roles
- ✅ Manage page organization and structure
- ✅ Configure system settings (file size limits, page size limits)
- ✅ Access admin dashboard with monitoring and analytics
- ✅ Manage orphaned pages

### Page Organization

#### Hierarchical Structure
- **Top-level pages**: Root pages that can be organized into sections
- **Sections**: Organizational grouping/category (e.g., "game-mechanics", "lore")
- **Parent**: Hierarchical parent-child relationship for navigation
- **Independence**: A page's section and parent are independent
  - A page can be in "game-mechanics" section but have a parent in "introduction" section
  - Section is for categorization, parent is for hierarchy
- **Default Behavior**: When creating a page, section can be inherited from parent if not specified
- **Child-parent relationships**: Pages can have parent pages, creating a tree structure
- **Link tracking**: Bidirectional link tracking between pages
  - Forward links: Links from this page to others
  - Backlinks: Pages that link to this page

#### Navigation
- **Book-reading format**: Continuous scroll (web page style, not page-turning)
- **Breadcrumb navigation**: Show current location in hierarchy
- **Previous/Next navigation**: Navigate through pages in hierarchical order

### Content Features

#### Table of Contents
- **Per-page TOC**: Auto-generated from page headings - no manual override
- **Heading Levels**: Includes H2, H3, H4, H5, H6 (H1 excluded, it's the page title)
- **Anchor Generation**: 
  - Extract heading text, convert to lowercase
  - Replace spaces with hyphens, remove special characters
  - Result: `## Combat Mechanics` becomes anchor `#combat-mechanics`
  - Old anchors remain valid for backward compatibility when headings change
- **Overall index**: Master index of all pages with search functionality
- **Local index**: Index of terms/concepts within a single page

#### Editor
- **WYSIWYG Editor**: Tiptap (modern, extensible rich text editor)
- **Formatting options**: 
  - Headings (H1-H6)
  - Bold, italic, underline
  - Lists (ordered, unordered)
  - Links (internal and external)
  - Images
  - Code blocks
  - Tables
- **Markdown support**: Underlying storage in Markdown with YAML frontmatter, but editing is visual
- **Editor choice**: Tiptap selected for modern features, extensibility, and React support
- **Section extraction**: 
  - Select text/sections and extract to new page
  - Extract selected headings and their content to new page
  - Replace extracted content with link to new page
- **TOC section promotion**: 
  - Button on each TOC entry to promote section to new child or sibling page
  - Automatically extracts section content and creates new page

#### Comments System
- **Comment placement**: Bottom of page (below content)
- **Threading**: Support for replies to comments (maximum depth: 5 levels)
- **Recommendations**: Special comment type for update suggestions
- **User attribution**: Show commenter name and timestamp

### Data Model

#### Page Structure
```
Page {
  id: UUID
  title: string
  slug: string (URL-friendly, auto-generated, unique, manually overridable)
  content: markdown
  parent_id: UUID (nullable, can be orphanage placeholder)
  section: string (optional, writers can create)
  order: integer (for sorting within parent)
  status: enum (draft, published)
  is_public: boolean (always true for now)
  word_count: integer (calculated: strip markdown, count words, images excluded)
  content_size_kb: float (calculated: raw markdown byte size / 1024, images excluded)
  created_at: timestamp
  updated_at: timestamp
  created_by: user_id
  updated_by: user_id
  version: integer
  version_history: PageVersion[] (full history with diffs, all versions kept)
  is_orphaned: boolean
  orphaned_from: UUID (original parent before deletion)
}
```

#### Orphanage System
```
Orphanage {
  id: UUID (special system page, parent_id = null)
  title: "Orphaned Pages"
  slug: "_orphanage"
  is_system_page: boolean (true)
  children: Page[] (orphaned pages)
}
```

#### Link Tracking
```
PageLink {
  from_page_id: UUID
  to_page_id: UUID
  link_text: string (the anchor text used)
  created_at: timestamp
}
```

#### Comments
```
Comment {
  id: UUID
  page_id: UUID
  parent_comment_id: UUID (nullable, for threading)
  user_id: UUID
  content: text
  is_recommendation: boolean
  created_at: timestamp
  updated_at: timestamp
}
```

#### Index Entries
```
IndexEntry {
  id: UUID
  page_id: UUID
  term: string
  context: string (surrounding text)
  position: integer (character offset)
  is_keyword: boolean (true for extracted keywords, false for full-text)
  is_manual: boolean (true if manually tagged, false if auto-extracted)
}
```

#### System Configuration
```
WikiConfig {
  Stored as key-value pairs in wiki_config table:
  - max_file_upload_size_mb: float (admin configurable)
  - max_page_size_kb: float (admin configurable, nullable)
  - page_size_resolution_due_date: timestamp (nullable, set when limit is enforced)
  - oversized_pages: UUID[] (pages exceeding max_page_size_kb, tracked in separate table)
}
```

#### Oversized Page Notification
```
OversizedPageNotification {
  id: UUID
  page_id: UUID
  current_size_kb: float
  max_size_kb: float
  resolution_due_date: timestamp
  notified_users: UUID[] (page authors)
  resolved: boolean
  created_at: timestamp
}
```

#### Version History
```
PageVersion {
  id: UUID
  page_id: UUID
  version: integer
  content: markdown (full content at this version)
  title: string
  changed_by: user_id
  change_summary: text (optional)
  diff_data: jsonb (stores diff information)
  created_at: timestamp
}
```

## User Interface Requirements

### Reading View
- Clean, book-like layout with comfortable reading width
- Sidebar with:
  - Table of contents (current page)
  - Navigation tree (hierarchical structure)
  - Search functionality
- Breadcrumb navigation at top
- Previous/Next page navigation
- Backlinks section showing pages that link here

### Editing View
- WYSIWYG editor with formatting toolbar
- Preview mode toggle
- Save draft functionality
- Version history view
- Link insertion dialog (with search for internal pages)
- Image upload and insertion

### Index View
- Searchable master index
- Alphabetical listing
- Filter by section/category
- Click to navigate to page

## API Requirements

### Authentication
- Integration with Auth Service for user authentication
- Role-based endpoint protection
- JWT token validation

### Key Endpoints (Detailed in API docs)
- Page CRUD operations
- Comment management
- Link tracking
- Search and indexing
- File upload (for images)

## Technical Considerations

### File Storage Structure
```
data/
  pages/
    section-name/
      page-slug.md
      child-page-slug.md
    another-section/
      page-slug.md
  uploads/
    images/
      {uuid}.{ext}  (UUID-based filenames)
      metadata/
        {uuid}.json  (original filename, page association, etc.)
```

### Image Storage
- **Location**: `data/uploads/images/` (centralized)
- **Naming**: UUID-based filenames (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`)
- **Metadata**: Stored in separate JSON files with original filename, page associations, upload date
- **Association**: Images linked to pages via database, not file structure

### Metadata Storage
- **YAML frontmatter** in each markdown file containing:
  - title
  - slug
  - parent_slug (not parent_id - slugs are easier for AI and file-based workflows)
  - section
  - order
  - created_by
  - updated_by
  - version
- **Database** for:
  - User permissions
  - Comments
  - Link relationships
  - Search index (full-text and keywords)
  - Page metadata (for fast queries)
  - Version history with diffs

### Performance
- Cache rendered HTML for frequently accessed pages
- Lazy-load comments
- Incremental search index updates
- Database indexing on frequently queried fields
- Full-text search using PostgreSQL (no weighted ranking, pure relevance)
- Keyword extraction: Automatic (NLP) + manual tagging support

## Decisions Made

1. ✅ **File format**: Markdown with YAML frontmatter for metadata
2. ✅ **Book-reading format**: Continuous scroll (web page style)
3. ✅ **TOC generation**: Auto-generated only (from headings)
4. ✅ **Index scope**: Full-text search (PostgreSQL relevance ranking)
5. ✅ **Keywords**: Both automatic extraction (NLP) and manual tagging
6. ✅ **WYSIWYG editor**: Tiptap selected
7. ✅ **Comment threading**: Maximum depth of 5 levels
8. ✅ **Version history**: Full history with diffs and rollback capability (keep all versions)
9. ✅ **Version comparison**: Both side-by-side and inline diff views
10. ✅ **Draft status**: Writers can save drafts (visible only to creator and admins)
11. ✅ **Page visibility**: All pages are public
12. ✅ **Slug generation**: Auto-generate from title, allow manual override, enforce uniqueness
13. ✅ **Section creation**: Writers can create sections
14. ✅ **Page deletion**: Orphanage system for child pages
15. ✅ **Image storage**: Centralized in `data/uploads/images/` with UUID-based naming
16. ✅ **File size limits**: Admin configurable (presets: 1MB, 2MB, 5MB, 10MB + custom)
17. ✅ **Page size limits**: Admin configurable with monitoring dashboard and notification system
18. ✅ **Section extraction**: Editor functions to extract sections to new pages
19. ✅ **TOC promotion**: Button to promote sections to child/sibling pages

## Future Enhancements (Not in MVP)

- Page templates
- Collaborative real-time editing
- Export to PDF/EPUB
- Page tags/categories
- Watchlist for page changes
- Page approval workflow (for writers)

