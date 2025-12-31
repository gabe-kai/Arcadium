---
created_by: admin
section: Wiki
slug: wiki-design
status: published
title: Wiki Design
updated_by: admin
---
# Wiki Design

This document provides a comprehensive overview of the Arcadium Wiki system, covering its features, functionality, and user interface design. The wiki serves as the central documentation hub for the Arcadium game project, combining a book-like reading experience with powerful content management capabilities.

## Introduction & Overview

### What is the Arcadium Wiki?

The Arcadium Wiki is a comprehensive documentation and planning system designed to serve as the single source of truth for game design, technical architecture, and operational knowledge. It provides a modern, intuitive interface for creating, organizing, and discovering information about the Arcadium game world.

### Design Principles

The wiki is built around three core design principles:

1. **Book-like Reading Experience**: Pages are designed for comfortable reading with optimal typography, generous spacing, and a continuous scroll format that feels natural and immersive.

2. **Easy Navigation**: Multiple navigation methods ensure users can always find what they're looking for, whether through hierarchical organization, search, or contextual links.

3. **Intuitive Editing**: A powerful WYSIWYG editor makes content creation and editing accessible to writers without requiring technical markdown knowledge, while still supporting advanced features.

### Target Audience

The wiki serves different user roles with tailored experiences:

- **Viewers** (Unregistered): Can read all public pages and browse content
- **Players** (Registered): Can read pages and leave comments with suggestions
- **Writers**: Can create, edit, and organize pages with full content management capabilities
- **Admins**: Have complete control over the wiki, including user management and system configuration

## Features & Functionality Overview

### Core Features

#### Hierarchical Page Organization

Pages are organized in a flexible hierarchical structure that supports both categorization and navigation:

- **Sections**: Organizational categories (e.g., "Game Mechanics", "Lore", "Architecture")
- **Parent-Child Relationships**: Pages can have parent pages, creating a tree structure for logical navigation
- **Independence**: A page's section and parent are independent - a page can be in one section but have a parent in another
- **Flexible Structure**: Writers can reorganize pages by changing parent relationships or sections without losing content

#### Full-Text Search and Indexing

Powerful search capabilities help users discover content quickly:

- **Global Search**: Search bar in the header with keyboard shortcut (Ctrl+K / Cmd+K)
- **Full-Text Search**: Searches through page content, titles, and metadata
- **Search Suggestions**: Real-time suggestions as you type
- **Recent Searches**: Dropdown showing recent search queries
- **Search Results**: Displays title, content snippet, section, and relevance score
- **Alphabetical Index**: Browse all pages alphabetically with section filtering
- **Pagination**: Search results are paginated for easy navigation

#### Version History and Comparison

Every page change is tracked with complete version history:

- **Automatic Versioning**: Every save creates a new version
- **Version Viewing**: View any previous version of a page
- **Version Comparison**: Compare two versions side-by-side or inline
- **Diff Display**: Visual highlighting of additions (green) and deletions (red)
- **Version Metadata**: See who made changes, when, and view change summaries
- **Restore Capability**: Writers and admins can restore previous versions

#### Comments and Collaboration

A threaded commenting system enables community engagement:

- **Threaded Comments**: Comments can be replied to, creating nested threads (up to 5 levels deep)
- **User Attribution**: Comments show user names and timestamps
- **Edit and Delete**: Users can edit or delete their own comments
- **Recommendations**: Players can mark comments as recommendations for page updates
- **Collapsible Threads**: Long comment threads can be collapsed for easier reading
- **Pagination**: Comments are paginated for pages with many comments

#### Role-Based Permissions

Granular permission system ensures appropriate access control:

- **Viewer Permissions**: Read all public pages
- **Player Permissions**: Read pages and leave comments
- **Writer Permissions**: Create, edit, and organize pages; save drafts; delete own pages
- **Admin Permissions**: Full system access including user management, page deletion, and system configuration

#### Page Metadata Management

Rich metadata system for organizing and categorizing content:

- **Title and Slug**: Human-readable title with URL-friendly slug (auto-generated or custom)
- **Section Assignment**: Categorize pages into sections
- **Parent Relationship**: Set hierarchical parent for navigation
- **Order Index**: Control display order within sections
- **Status**: Mark pages as "published" or "draft"
- **Custom Fields**: Additional metadata fields are preserved (tags, categories, etc.)

#### Link Tracking

Bidirectional link tracking helps users discover related content:

- **Forward Links**: See all links from the current page to other pages
- **Backlinks**: See all pages that link to the current page
- **Context Snippets**: Backlinks show where the link appears in the source page
- **Automatic Detection**: Links are automatically detected and tracked
- **Internal vs External**: Visual distinction between internal wiki links and external links

### Content Management

#### Markdown with YAML Frontmatter

Pages are stored as markdown files with YAML frontmatter for metadata:

- **Markdown Content**: Rich text formatting with support for headings, lists, links, images, tables, and code blocks
- **YAML Frontmatter**: Metadata stored at the top of files (title, slug, section, status, etc.)
- **File-Based Storage**: Pages stored as files in `data/pages/` directory, enabling version control and AI access
- **Database Sync**: Files automatically sync to database for web access
- **Preservation**: Custom frontmatter fields are preserved when users edit through the UI

#### WYSIWYG Editor (Tiptap)

Powerful visual editor makes content creation accessible:

- **Visual Editing**: Edit content visually without seeing markdown code
- **Rich Formatting**: Headings, bold, italic, code, lists, links, images, tables
- **Code Blocks**: Insert code blocks with syntax highlighting support
- **Table Support**: Insert and edit tables with customizable dimensions
- **Link Insertion**: Search for internal pages when inserting links
- **Image Upload**: Upload images with preview
- **Undo/Redo**: Full undo/redo support
- **Real-Time Preview**: Toggle between editor and preview modes
- **Auto-Save Drafts**: Drafts automatically saved to browser storage

#### Draft/Published Status

Content workflow support for writers:

- **Draft Status**: Save pages as drafts before publishing
- **Published Status**: Make pages visible to all users
- **Status Indicator**: Visual indicator shows page status
- **Draft Badge**: Draft pages show a badge in navigation

#### Section Extraction

Advanced content organization features:

- **Extract Sections**: Extract a section of content to a new page
- **TOC Promotion**: Promote table of contents items to child or sibling pages
- **Automatic Linking**: Extracted content automatically links back to source

#### Page Archiving and Deletion

Content lifecycle management:

- **Archive Pages**: Hide pages from normal views without deleting
- **Unarchive Pages**: Restore archived pages
- **Delete Pages**: Permanently remove pages (with permission checks)
- **Orphan Management**: System handles orphaned pages when parents are deleted

### Navigation Features

#### Navigation Tree (Left Sidebar)

Hierarchical navigation in a collapsible tree:

- **Expandable/Collapsible**: Click to expand or collapse sections
- **Current Page Highlighting**: Active page is highlighted in the tree
- **Auto-Expand**: Path to current page automatically expands
- **Search Within Tree**: Filter tree to find pages quickly
- **Page Counts**: See how many pages are in each section
- **Draft Indicators**: Visual badges show draft pages
- **Persistent State**: Expanded state saved in browser storage

#### Breadcrumb Navigation

Shows your location in the page hierarchy:

- **Hierarchical Path**: Displays "Home > Section > Parent > Current Page"
- **Clickable Links**: Click any breadcrumb to navigate
- **Auto-Hide**: Hidden when only showing the root page

#### Previous/Next Navigation

Navigate through pages in order:

- **Order-Based**: Based on page order index within sections
- **Previous Button**: Navigate to previous page in sequence
- **Next Button**: Navigate to next page in sequence
- **Disabled States**: Buttons disabled at first/last pages

#### Table of Contents (Auto-Generated)

Quick navigation within the current page:

- **Auto-Generated**: Created automatically from page headings (H2-H6)
- **Click to Scroll**: Click any TOC item to scroll to that section
- **Active Highlighting**: Current section highlighted while scrolling
- **Nested Structure**: Indentation shows heading hierarchy
- **Sticky Positioning**: TOC stays visible while scrolling
- **Collapsible**: Can be collapsed on shorter pages

#### Backlinks Display

Discover related content:

- **Linking Pages**: See all pages that link to the current page
- **Context Snippets**: See where the link appears in source pages
- **Click to Navigate**: Click any backlink to visit that page
- **Count Display**: See total number of backlinks

#### Global Search

Find content quickly:

- **Header Search Bar**: Always accessible in the header
- **Keyboard Shortcut**: Ctrl+K (Windows/Linux) or Cmd+K (Mac)
- **Search Suggestions**: Real-time suggestions as you type
- **Recent Searches**: Quick access to recent queries
- **Results Page**: Dedicated page showing search results with highlighting
- **Pagination**: Navigate through multiple pages of results

#### Alphabetical Index

Browse all pages alphabetically:

- **Letter Navigation**: Click letters to jump to that section
- **Section Filtering**: Filter by section
- **Page Counts**: See how many pages start with each letter
- **Search Within Index**: Search while viewing the index

## UI/UX Design

### Layout Structure

#### Reading View (Three-Column Layout)

The reading view provides an optimal experience for consuming content:

```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Arcadium Wiki    [Search] [User Menu] [Theme]   │
├─────────────────────────────────────────────────────────┤
│  Home > Section > Parent > Current Page                 │
├──────────┬──────────────────────────────┬───────────────┤
│          │                              │               │
│  Nav     │                              │  Sidebar      │
│  Tree    │      Page Content            │  - TOC        │
│          │      (Optimal Reading Width) │  - Backlinks  │
│          │                              │               │
│          │      [Edit] [Delete] [Archive]              │
│          │                              │               │
│          │      [Previous] [Next]       │               │
│          │                              │               │
│          ├──────────────────────────────┤               │
│          │      Comments Section        │               │
│          │      (Threaded, max 5 deep)  │               │
│          │                              │               │
└──────────┴──────────────────────────────┴───────────────┘
```

**Key Features:**
- **Left Column**: Navigation tree (collapsible on mobile)
- **Center Column**: Main content area (max-width 800px for optimal reading)
- **Right Column**: Table of Contents and Backlinks (collapsible on mobile)
- **Responsive**: Adapts to different screen sizes

#### Editing View (Full-Width Editor)

The editing view maximizes space for content creation:

```
┌─────────────────────────────────────────────────────────┐
│  [Save] [Cancel] [Preview] [History] [Tiptap Toolbar]   │
├─────────────────────────────────────────────────────────┤
│  Title: [_____________________________]                  │
│  Slug:  [wiki-design] (auto-generated)                   │
│  Parent: [Select parent page...]                        │
│  Section: [Wiki]                                        │
│  Order: [1]                                              │
│  Status: ○ Published  ○ Draft                            │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │  Tiptap WYSIWYG Editor                          │   │
│  │  (Visual editing area with formatting tools)    │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  Version: 5 (View History)                              │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Full-Width Layout**: Maximum space for editing
- **Metadata Form**: All page metadata editable at the top
- **Rich Toolbar**: Comprehensive formatting tools
- **Auto-Save**: Drafts saved automatically
- **Preview Toggle**: Switch between editor and preview

### Component Design

#### Navigation Tree

**Purpose**: Show hierarchical page structure

**Features**:
- Expandable/collapsible tree nodes with smooth animations
- Current page highlighted with active state
- Click to navigate to any page
- Search/filter within tree with auto-expand matching branches
- Page count per section
- Draft badge indicators
- Persistent expanded state (localStorage)
- Folder icons for sections, document icons for pages

**Visual Design**:
- Clean, minimal tree view
- Hover effects on tree items
- Active state highlighting
- Smooth expand/collapse animations

#### Main Content Area

**Reading Mode**:
- **Max Width**: 800px (optimal reading width)
- **Line Height**: 1.6-1.8 (comfortable reading)
- **Typography**: Clear, readable font with proper hierarchy
- **Spacing**: Generous margins and padding
- **Code Blocks**: Syntax highlighting with Prism.js
- **Images**: Responsive with max-width 100%, rounded corners, shadows
- **Tables**: Styled with striped rows, hover effects, borders
- **Blockquotes**: Enhanced styling with background and decorative quote mark
- **Links**: Visual distinction between internal and external links

**Content Features**:
- Auto-generated table of contents (if page has multiple headings)
- Inline link styling
- Responsive image handling
- Table formatting (GFM markdown tables)
- Enhanced block quotes

#### Table of Contents Sidebar

**Purpose**: Quick navigation within current page

**Features**:
- Auto-generated from H2, H3, H4, H5, H6 headings (H1 excluded)
- Click to scroll to section (smooth scroll)
- Highlight current section while scrolling
- Indentation for nested headings
- Active section highlighting
- Sticky positioning (stays visible while scrolling)
- Collapsible if page is short (< 5 TOC items)

**Visual Design**:
- Sticky positioning
- Clear indentation for hierarchy
- Active section highlighted
- Smooth scroll behavior

#### Backlinks Section

**Purpose**: Show pages that link to current page

**Features**:
- List of linking pages
- Context snippets (where link appears)
- Click to navigate to linking page
- Count of backlinks displayed
- Styled list with hover effects

**Visual Design**:
- Clean list layout
- Hover effects on items
- Context snippets styled differently

#### Comments Section

**Layout**:
- Below main content
- Threaded replies (indented, maximum 5 levels deep)
- User avatars/names
- Timestamps (relative and absolute)
- Edit/delete for own comments
- "Recommend update" button (for players)

**Features**:
- Collapsible threads
- Reply button on each comment (disabled at max depth)
- Mark as recommendation (special styling)
- Pagination for long comment threads (10 comments per page)
- Visual indicator for thread depth
- Sign-in prompt for unauthenticated users

**Visual Design**:
- Light background for comments section
- Clear separation between threads
- Highlight recommendations
- Responsive layout

#### Search Interface

**Global Search**:
- Search bar in header
- Dropdown with recent searches (max 10 items)
- Search suggestions as you type (debounced, 300ms)
- Clear button
- Keyboard shortcut (Ctrl+K / Cmd+K)
- Results show: title, snippet, section, relevance score
- Search term highlighting in results
- Pagination (20 results per page)

**Index View**:
- Alphabetical listing of all pages
- Filter by section
- Click letter to jump to section
- Show page count per letter
- Search within index

#### Editor Toolbar and Controls

**Toolbar Features**:
- Format dropdown (H1-H6, Paragraph)
- Text formatting: Bold, Italic, Code
- Lists: Bullet list, Numbered list
- Link insertion (with internal page search dialog)
- Image upload/insert (with preview)
- Code block insertion
- Table insertion (customizable rows/columns, 1-20 each)
- Table controls (when cursor in table):
  - Add/Delete columns (before/after current column)
  - Add/Delete rows (before/after current row)
  - Delete entire table
- Undo/Redo buttons

**Editing Experience**:
- Visual editing (no markdown code visible)
- Real-time preview toggle
- Auto-save drafts (localStorage)
- Link insertion dialog with page search
- Image upload with preview
- Table insertion dialog with customization
- Responsive toolbar (adapts to screen size)

### User Experience

#### Reading Flow

1. User lands on wiki homepage or navigates to a page
2. Browse navigation tree or use search to find content
3. Click page to read
4. Scroll through content with comfortable reading width
5. Use table of contents to jump to specific sections
6. View backlinks to discover related content
7. Read comments at bottom of page
8. Navigate via Previous/Next buttons or breadcrumbs
9. Use search or index to discover more content

#### Commenting Flow (Player)

1. Scroll to comments section at bottom of page
2. Type comment in text area
3. Optionally mark as "recommendation" (for players)
4. Submit comment
5. See comment appear in thread immediately
6. Reply to other comments (up to 5 levels deep)
7. Edit or delete own comments as needed

#### Editing Flow (Writer)

1. Click "Edit" button on page (visible to writers/admins)
2. Editor opens with current content loaded
3. Make changes using WYSIWYG formatting tools
4. Update metadata (title, section, parent, order, status) if needed
5. Preview changes using preview toggle
6. Save page (creates new version automatically)
7. Redirected to updated page
8. View version history to see all changes

#### Page Creation Flow (Writer)

1. Click "New Page" button in header (visible to writers/admins)
2. Metadata form appears with empty fields
3. Enter title (slug auto-generated)
4. Optionally select parent page (for hierarchy)
5. Choose or enter section name
6. Set order index (optional)
7. Choose status (published or draft)
8. Write content in WYSIWYG editor
9. Save page
10. Redirected to newly created page

#### Search and Discovery Flow

1. Use search bar in header or press Ctrl+K / Cmd+K
2. Type search query (see suggestions as you type)
3. View search results with highlighted terms
4. Click result to navigate to page
5. Or browse alphabetical index
6. Filter index by section if needed
7. Use navigation tree to explore by hierarchy

### Visual Design

#### Typography

- **Headings**: Bold, clear hierarchy (H1-H6)
- **Body Text**: Readable serif or sans-serif font
- **Code**: Monospace font for code blocks
- **Line Spacing**: Comfortable line height (1.6-1.8)
- **Font Sizes**: Responsive scaling for different screen sizes

#### Color Scheme

- **Primary Colors**: Theme-based (adapts to light/dark mode)
- **Text**: High contrast for readability
- **Links**: Distinct color with hover effects
- **Comments**: Light background for separation
- **Editor**: Clean white/theme background
- **Code Blocks**: Syntax highlighting with theme colors
- **Tables**: Alternating row colors for readability

#### Spacing

- **Generous Whitespace**: Comfortable padding and margins
- **Clear Separation**: Distinct sections with visual separation
- **Comfortable Padding**: Adequate padding in editor and content areas
- **Responsive Spacing**: Adapts to screen size

#### Accessibility

- **Keyboard Navigation**: Full keyboard support for all features
- **Screen Reader Support**: ARIA labels on interactive elements
- **Focus Indicators**: Clear focus states on all focusable elements
- **High Contrast**: Meets WCAG AA contrast ratios
- **Alt Text**: Image alt text support
- **Semantic HTML**: Proper HTML structure for assistive technologies

#### Theme Support

- **Light/Dark Mode**: Toggle between light and dark themes
- **System Preference**: Automatically detects system theme preference
- **Persistent Choice**: Theme preference saved in browser
- **Consistent Styling**: All components adapt to theme

## User Roles & Permissions

### Viewer (Unregistered)

**Permissions**:
- ✅ View all public pages
- ✅ Browse navigation tree
- ✅ Use search and index
- ✅ View table of contents and backlinks
- ❌ Cannot comment
- ❌ Cannot edit or create pages
- ❌ Cannot delete pages

**Experience**: Read-only access to all wiki content with full navigation and discovery features.

### Player (Registered)

**Permissions**:
- ✅ All Viewer permissions
- ✅ Leave comments on pages
- ✅ Reply to comments (threaded)
- ✅ Mark comments as recommendations
- ✅ Edit own comments
- ✅ Delete own comments
- ❌ Cannot edit or create pages
- ❌ Cannot delete pages

**Experience**: Can engage with content through comments and suggestions, but cannot modify pages.

### Writer

**Permissions**:
- ✅ All Player permissions
- ✅ Edit existing pages
- ✅ Create new pages
- ✅ Create new sections
- ✅ Save pages as drafts
- ✅ Extract sections to new pages
- ✅ Promote sections to child/sibling pages
- ✅ Delete own pages
- ✅ Archive own pages
- ✅ View version history
- ✅ Restore previous versions
- ❌ Cannot delete pages written by others
- ❌ Cannot archive pages written by others

**Experience**: Full content management capabilities for creating and organizing wiki content.

### Admin

**Permissions**:
- ✅ All Writer permissions
- ✅ Delete any page (including those written by others)
- ✅ Archive any page
- ✅ Unarchive any page
- ✅ Manage user roles
- ✅ Manage page organization and structure
- ✅ Configure system settings (file size limits, page size limits)
- ✅ Access admin dashboard with monitoring and analytics
- ✅ Manage orphaned pages
- ✅ View service status and health

**Experience**: Complete system control with administrative tools and monitoring capabilities.

## Technical Highlights

### File-Based Storage with Database Sync

- **Local File Storage**: Pages stored as markdown files in `data/pages/` directory
- **File System Mirroring**: Directory structure mirrors page hierarchy
- **Database Sync**: Files automatically sync to database for web access
- **Version Control**: Files can be version controlled in git
- **AI Access**: Files accessible to AI agents for content generation

### Automatic File Watcher

- **Real-Time Syncing**: File watcher monitors directory for changes
- **Automatic Updates**: Files sync automatically when created or modified
- **Debouncing**: Prevents rapid-fire syncs (waits 1 second after last change)
- **Orphan Cleanup**: Automatically cleans up orphaned pages when files are deleted
- **Manual Sync**: Can also manually sync files or directories

### Markdown Processing and Rendering

- **Full Markdown Support**: All standard markdown features supported
- **GFM Tables**: GitHub Flavored Markdown table syntax
- **Code Blocks**: Language-specified code blocks with syntax highlighting
- **HTML Conversion**: Markdown converted to HTML for display
- **Link Processing**: Automatic internal link detection and processing
- **Image Handling**: Responsive image rendering with proper sizing

### Code Block Syntax Highlighting

- **Multiple Languages**: Support for JavaScript, TypeScript, Python, Bash, JSON, Markdown, CSS, SQL, and more
- **Prism.js Integration**: Frontend uses Prism.js for syntax highlighting
- **Language Classes**: Code blocks include language classes for highlighting
- **Whitespace Preservation**: Code formatting preserved exactly
- **Multi-Line Support**: Full support for multi-line code blocks

### Table Support (GFM Markdown)

- **Table Creation**: Insert tables with customizable dimensions (1-20 rows/columns)
- **Table Editing**: Full table manipulation (add/delete rows/columns)
- **Markdown Conversion**: Full round-trip support (HTML ↔ GFM markdown)
- **Proper Rendering**: Tables render with proper HTML structure (`<thead>`, `<tbody>`, etc.)
- **Styled Display**: Tables styled with striped rows, hover effects, and borders

## Conclusion

The Arcadium Wiki provides a comprehensive, user-friendly platform for documentation and knowledge management. With its intuitive interface, powerful features, and flexible organization system, it serves as the central hub for all project information. Whether you're a player looking for game information, a writer creating content, or an admin managing the system, the wiki is designed to make your work efficient and enjoyable.

The combination of file-based storage, automatic syncing, rich editing capabilities, and comprehensive navigation features creates a modern documentation system that scales with the project while remaining accessible to all users.
