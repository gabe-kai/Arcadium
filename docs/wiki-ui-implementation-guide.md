# Wiki UI Implementation Guide

This guide outlines the implementation plan for building the Wiki User Interface based on the specifications in `wiki-user-interface.md`. The backend API is complete and ready to consume.

## Current Status

### ✅ Backend API (Complete)
- All API endpoints implemented and tested (561 tests passing)
- Page CRUD operations
- Comments system with threading
- Search and indexing
- Navigation and hierarchy
- Version history
- File uploads
- Admin dashboard endpoints
- Service status endpoints

### 🧩 Frontend UI (In Progress - Phases 1-6, 7-9, 10, 10.5 Complete)
**Test Coverage**: 560+ passing unit/integration tests across 35 test files, 32+ E2E tests

#### ✅ Phase 1: Foundation & Setup (Complete)
- React + Vite client bootstrapped in `client/`
- Basic project structure created (`components`, `pages`, `services`, `utils`, `test`)
- React Router configured with core routes (home, page view, edit, search, index)
- Base layout components implemented (header, footer, layout, sidebar placeholder)
- Initial styling in place for a modern, book-like reading shell
- Axios API client configured with `VITE_WIKI_API_BASE_URL` fallback to `http://localhost:5000/api`
- Testing infrastructure set up (Vitest + React Testing Library) with smoke tests for routing, layout, and API client
- **CORS configured** - Flask backend allows requests from React dev server (`localhost:3000`)
- **React Query integration** - Server state management for page data fetching
- **Auth context** - JWT token storage and Authorization header support ready
- **E2E Testing** - Playwright E2E tests for full user flows (syntax highlighting, navigation, TOC, backlinks)

#### ✅ Phase 2: Reading View - Core Components (Complete)
- **PageView component** - Full reading experience with content rendering, metadata display
- **Edit button** - Edit button in page header (shown for writers/admins with edit permissions)
- **Delete/Archive buttons** - Delete and archive buttons in page header (shown based on permissions)
- **Breadcrumb Navigation** - Component implemented with API integration, tests included
- **Previous/Next Navigation** - Component implemented with API integration, tests included
- **Enhanced Content Styling**:
  - Syntax highlighting (Prism.js with multiple languages: JS, TS, Python, Bash, JSON, Markdown, CSS, SQL)
  - Responsive image handling (max-width 100%, rounded corners, shadows)
  - Styled tables (striped rows, hover effects, borders)
  - Enhanced blockquotes (background, decorative quote mark)
  - Internal vs external link distinction (visual indicators, external icon)
- **API Integration**:
  - `usePage`, `useBreadcrumb`, `usePageNavigation` hooks
  - Automatic syntax highlighting and link processing after render
- **Tests added**:
  - PageView component tests (loading, error, success states)
  - Breadcrumb component tests (7 test cases)
  - PageNavigation component tests (8 test cases)
  - Backend: cache service tests (user_id=None), CORS header tests, unauthenticated page access tests

#### ✅ Phase 3: Navigation Tree (Left Sidebar) (Complete)
- **NavigationTree component** - Hierarchical page navigation with expandable/collapsible nodes
- **Tree Search** - Search/filter within tree with auto-expand matching branches
- **Tree Features**:
  - Expandable/collapsible tree nodes with smooth animations
  - Highlights current page
  - Auto-expands path to current page
  - Persists expanded state in localStorage
  - Draft badge indicator for draft pages
  - Hover effects and active state highlighting
- **API Integration**:
  - `useNavigationTree` hook with 5-minute cache
- **Tests added**:
  - NavigationTree component tests (11 test cases covering all features)

#### ✅ Phase 4: Table of Contents & Backlinks (Right Sidebar) (Complete)
- **TableOfContents component** - Auto-generated from page headings (H2-H6)
  - Click to scroll to section (smooth scroll)
  - Highlight current section while scrolling
  - Indentation for nested headings
  - Active section highlighting
  - Sticky positioning support
- **Backlinks component** - Displays pages that link to current page
  - Shows backlink count
  - Click to navigate to linking page
  - Styled list with hover effects
- **Integration**:
  - Both components integrated into PageView right sidebar
  - Rendered when `table_of_contents` or `backlinks` data is available from API
- **Tests added**:
  - TableOfContents component tests (10 test cases)
  - Backlinks component tests (9 test cases)
  - PageView integration tests for TOC and Backlinks

#### ✅ Phase 5: Comments System (Complete)
- **CommentsList component** - Displays all comments for a page with threading
- **CommentItem component** - Displays single comment with nested replies (up to 5 levels)
- **CommentForm component** - Form for creating new comments and replies
- **Features**:
  - Threaded comments with visual indentation
  - Collapsible reply threads
  - Edit own comments (inline editing)
  - Delete own comments (with confirmation)
  - Recommendation badge and styling (for player suggestions)
  - Relative and absolute timestamps
  - Reply button disabled at max depth (5 levels)
  - Sign-in prompt for unauthenticated users
- **API Integration**:
  - `useComments` hook for fetching comments
  - `useCreateComment`, `useUpdateComment`, `useDeleteComment` mutations
  - Automatic refetch on mutations
- **Integration**:
  - Fully integrated into PageView component
  - Rendered below page content
- **Tests added**:
  - CommentsList component tests (7 tests)
  - CommentItem component tests (15 tests)
  - CommentForm component tests (16 tests)
  - Comments API service tests

#### ✅ Phase 7: WYSIWYG Editor Integration (Complete)
- **Editor Component** - Tiptap-based rich text editor
  - Markdown import/export
  - All formatting tools (headings, bold, italic, code, lists, links, images, tables)
  - Code blocks with syntax highlighting
  - Undo/redo functionality
- **EditorToolbar Component** - Full formatting toolbar
  - Format dropdown (H1-H6, Paragraph)
  - Text formatting buttons
  - List buttons
  - Link and image insertion
  - Code block and table insertion
- **EditPage Component** - Full editing interface
  - Editor integration
  - Auto-save drafts to localStorage
  - Save/create page functionality
- **Tests added**:
  - Editor component tests (14 test cases)
  - EditorToolbar component tests (33 test cases)
  - EditPage component tests (22 test cases)
  - Integration tests for page editing flow (6 test cases)

#### ✅ Phase 8: Page Metadata Editor (Complete)
- **MetadataForm Component** - Complete metadata editing form
  - Title input (required, auto-generates slug)
  - Slug input (editable, real-time validation)
  - Parent page searchable dropdown (debounced search)
  - Section text input
  - Order number input (positive integers only)
  - Status radio buttons (published/draft)
  - Validation messages and error display
- **Features**:
  - Auto-generate slug from title (for new pages)
  - Debounced slug uniqueness validation (500ms)
  - Debounced parent page search (300ms)
  - Real-time validation feedback
  - Click-outside to close dropdown
- **Integration**:
  - Fully integrated into EditPage component
  - Metadata saved with page content
  - Auto-save includes metadata
  - Draft loading includes metadata
- **Tests added**:
  - MetadataForm component tests (40+ test cases)
  - Slug utility tests (20 test cases)
  - API function tests (searchPages, validateSlug - 10 test cases)
  - Integration tests for metadata in edit flow (5 test cases)

## Implementation Phases

### Phase 1: Foundation & Setup
**Goal**: Set up the frontend framework and basic infrastructure

#### Tasks:
- [x] Choose frontend framework (React 18 + React Router, Vite)
- [x] Set up project structure (components, pages, services, utils, test)
- [x] Configure build tools (Vite + `@vitejs/plugin-react-swc`)
- [x] Set up routing (React Router with core routes + v7 future flags)
- [x] Set up state management (React Query for server state, simple Auth context for auth state)
- [x] Configure API service layer (Axios wrapper in `src/services/api/client.js` with auth header support)
- [x] Set up authentication integration (JWT token storage + Axios Authorization header hookup)
- [x] Create base layout components (Header, Footer, Layout, Sidebar placeholder)
- [x] Set up CSS/styling approach (global CSS with modern, book-like layout)
- [x] Configure environment variables for API endpoints (`VITE_WIKI_API_BASE_URL`)
- [x] Set up UI testing infrastructure (Vitest + React Testing Library) and smoke tests

#### Deliverables:
- Working development environment (`npm install`, `npm run dev` in `client/`)
- Basic routing structure with placeholder pages
- API service layer with error handling hook (Axios client + interceptor)
- Testable layout shell (header, sidebar, content, footer)
- UI test harness ready for future components (Vitest + RTL)

---

### Phase 2: Reading View - Core Components
**Goal**: Implement the main reading experience

#### Tasks:
- [x] **Page Content Component** ✅ (Complete)
  - [x] Render markdown HTML content from backend API
  - [x] Display page title and metadata (updated_at, word_count, size, status)
  - [x] Apply basic typography styles (via global CSS)
  - [x] Syntax highlighting for code blocks (Prism.js with multiple languages)
  - [x] Responsive image handling (max-width 100%, rounded corners, shadows)
  - [x] Table styling (striped rows, hover effects, borders)
  - [x] Enhanced block quote styling (background, decorative quote mark)
  - [x] Internal vs external link styling (visual distinction, external icon)

- [x] **Breadcrumb Navigation** ✅
  - [x] Build breadcrumb trail from page hierarchy
  - [x] Click to navigate to parent pages
  - [x] Display: `Home > Section > Parent > Current Page`
  - [x] Hide when only root page (single item)
  - [x] Style with separators and hover effects

- [x] **Previous/Next Navigation** ✅
  - [x] Calculate previous/next pages based on order_index
  - [x] Display buttons at bottom of content
  - [x] Handle edge cases (first/last pages - disabled state)
  - [x] Style with hover effects and disabled states

- [x] **Page Header** (Basic implementation complete)
  - [x] Display page title
  - [x] Show metadata (last updated, word count, size)
  - [x] Status indicator (published/draft)
  - [x] Edit button (for writers/admins) - ✅ Complete (auth integration complete)

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Get page content ✅ (in use)
- `GET /api/pages/{page_id}/breadcrumb` - Get breadcrumb path (for breadcrumb nav)
- `GET /api/pages/{page_id}/navigation` - Get previous/next pages (for prev/next nav)
- `GET /api/navigation` - Get full navigation tree (for sidebar)

#### Deliverables:
- ✅ Fully styled page reading view - **COMPLETE**
- ✅ Working navigation (breadcrumbs, prev/next) - **COMPLETE**
- ✅ Responsive layout (basic) - **COMPLETE**
- ✅ Component tests for all navigation components - **COMPLETE**
- ✅ Enhanced content styling (syntax highlighting, tables, images, blockquotes, links) - **COMPLETE**

**Phase 2 Status: ✅ COMPLETE**

---

### Phase 3: Navigation Tree (Left Sidebar)
**Goal**: Implement hierarchical page navigation

#### Tasks:
- [x] **Navigation Tree Component** ✅
  - [x] Fetch and build page hierarchy
  - [x] Expandable/collapsible tree nodes
  - [x] Highlight current page
  - [x] Click to navigate
  - [x] Hover effects
  - [x] Active state highlighting
  - [x] Auto-expand path to current page
  - [x] Icons for pages vs sections - ✅ Complete (folder icon for sections, document icon for pages)

- [x] **Tree Search** ✅
  - [x] Search/filter within tree
  - [x] Auto-expand matching branches
  - [x] Filter non-matching branches

- [x] **Tree Features** ✅
  - [x] Remember expanded state (localStorage)
  - [x] Draft badge indicator
  - [x] Show page count per section - ✅ Complete (displays count of all descendant pages)
  - [ ] Lazy load children - **TODO** (not needed yet, performance is good)

#### API Endpoints Used:
- `GET /api/navigation` - Get hierarchical structure ✅ (in use)

#### Deliverables:
- ✅ Functional navigation tree
- ✅ Search within tree
- ✅ Smooth expand/collapse (CSS transitions)
- ✅ Expanded state persistence
- ✅ Current page highlighting

**Phase 3 Status: ✅ COMPLETE** (except optional enhancements)

---

### Phase 4: Table of Contents & Backlinks (Right Sidebar)
**Goal**: Implement right sidebar with TOC and backlinks

#### Tasks:
- [x] **Table of Contents Component** ✅
  - [x] Auto-generate from page headings (H2-H6)
  - [x] Click to scroll to section (smooth scroll)
  - [x] Highlight current section while scrolling
  - [x] Sticky positioning (stays visible)
  - [x] Indentation for nested headings
  - [x] Active section highlighting
  - [x] Collapsible if page is short - ✅ Complete (collapsible for pages with < 5 TOC items)

- [x] **Backlinks Component** ✅
  - [x] Display pages that link to current page
  - [x] Show context snippet (where link appears) - ✅ Complete (frontend ready, requires backend support for context data)
  - [x] Click to navigate to linking page
  - [x] Display backlink count
  - [x] Styled list with hover effects

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Includes `table_of_contents` and `backlinks` ✅ (in use)

#### Deliverables:
- ✅ Sticky TOC with scroll highlighting
- ✅ Functional backlinks section
- ✅ Smooth scroll-to-section behavior
- ✅ Component tests for both TOC and Backlinks

**Phase 4 Status: ✅ COMPLETE** (except optional enhancements)

---

### Phase 5: Comments System
**Goal**: Implement threaded comments below page content

#### Tasks:
- [x] **Comments List Component** ✅
  - [x] Display threaded comments (max 5 levels deep)
  - [x] Visual indentation for thread depth
  - [x] User avatars/names
  - [x] Timestamps (relative and absolute)
  - [x] Collapsible threads
  - [x] Pagination for long threads - ✅ Complete (10 comments per page with navigation)

- [x] **Comment Form Component** ✅
  - [x] Text area for new comment
  - [x] Reply button on each comment (disabled at max depth)
  - [x] "Recommend update" checkbox (for players)
  - [x] Submit button
  - [x] Loading states
  - [x] Error handling

- [x] **Comment Actions** ✅
  - [x] Edit own comments (inline editing)
  - [x] Delete own comments (with confirmation)
  - [x] Mark as recommendation (special styling)
  - [x] Visual indicator for thread depth

- [x] **Comment Styling** ✅
  - [x] Light background for comments section
  - [x] Clear separation between threads
  - [x] Highlight recommendations
  - [x] Responsive layout

#### API Endpoints Used:
- `GET /api/pages/{page_id}/comments` - List comments ✅ (in use)
- `POST /api/pages/{page_id}/comments` - Create comment ✅ (in use)
- `PUT /api/comments/{comment_id}` - Update comment ✅ (in use)
- `DELETE /api/comments/{comment_id}` - Delete comment ✅ (in use)

#### Deliverables:
- ✅ Fully functional threaded comments
- ✅ Reply, edit, delete functionality
- ✅ Recommendation styling
- ✅ Integration with PageView
- ✅ Comprehensive test coverage
- [ ] Pagination - **TODO** (optional enhancement)

**Phase 5 Status: ✅ COMPLETE** (except optional pagination enhancement)

---

### Phase 6: Search Interface
**Goal**: Implement global search functionality

#### Tasks:
- [x] **Search Bar Component** ✅
  - [x] Search input in header
  - [x] Keyboard shortcuts (Ctrl+K / Cmd+K)
  - [x] Dropdown with recent searches (localStorage) - ✅ **Optional enhancement complete**
  - [x] Search suggestions as you type (debounced) - ✅ **Optional enhancement complete**
  - [x] Clear button - ✅ **Optional enhancement complete**

- [x] **Search Results Page** ✅
  - [x] Display search results
  - [x] Show: title, snippet, section, relevance score
  - [x] Highlight search terms
  - [x] Click to navigate to page
  - [x] "No results" state
  - [x] Pagination - ✅ **Optional enhancement complete**

- [x] **Index View** ✅
  - [x] Alphabetical listing of all pages
  - [x] Filter by section
  - [x] Click letter to jump to section
  - [x] Search within index
  - [x] Show page count per letter - ✅ **Optional enhancement complete**

#### API Endpoints Used:
- `GET /api/search?q={query}` - Full-text search ✅ (in use)
- `GET /api/index` - Get index entries ✅ (in use)

#### Deliverables:
- ✅ Global search bar in header
- ✅ Search results page with highlighting
- ✅ Alphabetical index view with filters
- ✅ Search API integration
- ✅ Comprehensive test coverage

**Phase 6 Status: ✅ COMPLETE** (including all optional enhancements)

---

### Phase 7: WYSIWYG Editor Integration
**Goal**: Integrate Tiptap editor for page editing

#### Tasks:
- [x] **Install Tiptap Dependencies** ✅
  - [x] Install `@tiptap/react` and core packages
  - [x] Install extensions (bold, italic, lists, links, images, tables, code)
  - [x] Install markdown conversion utilities (marked, turndown)

- [x] **Editor Component** ✅
  - [x] Initialize Tiptap editor
  - [x] Configure toolbar with all required buttons
  - [x] Format dropdown (H1-H6, Paragraph)
  - [x] Bold, Italic, Code buttons
  - [x] Bullet list, Numbered list buttons
  - [x] Link button (with prompt dialog)
  - [x] Image insert button (with prompt dialog)
  - [x] Code block button
  - [x] Table button
  - [x] Undo/Redo buttons

- [x] **Editor Features** ✅
  - [x] Load markdown content into editor
  - [x] Export editor content to markdown
  - [x] Auto-save drafts (localStorage)
  - [x] Link insertion (basic prompt)
  - [x] Image insertion (basic prompt)
  - [x] Table editor (visual grid)
  - [x] Keyboard shortcuts (Tiptap built-in)
  - [x] Real-time preview toggle - ✅ Complete (toggle between editor and preview)
  - [x] Link insertion dialog with page search - ✅ Complete (searchable dialog for internal/external links)
  - [x] Image upload with preview - ✅ Complete (file upload with preview and URL input)

- [x] **Editor Styling** ✅
  - [x] Clean background with theme colors
  - [x] Comfortable padding
  - [x] Toolbar styling
  - [x] Content area styling
  - [x] Focus states

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Load page for editing ✅ (in use)
- `PUT /api/pages/{page_id}` - Save page updates ✅ (in use)
- `POST /api/pages` - Create new page ✅ (in use)
- `POST /api/upload/images` - Upload images (not yet implemented)

#### Deliverables:
- ✅ Fully functional Tiptap editor
- ✅ All formatting tools working
- ✅ Link and image insertion (basic)
- ✅ Auto-save drafts
- ✅ Comprehensive test coverage (14+ tests for Editor, 33+ tests for EditorToolbar)

**Phase 7 Status: ✅ COMPLETE** (except optional enhancements)

---

### Phase 8: Page Metadata Editor
**Goal**: Implement form for editing page metadata

#### Tasks:
- [x] **Metadata Form Component** ✅
  - [x] Title input (required)
  - [x] Slug input (auto-generated from title, editable)
  - [x] Parent page dropdown (with search)
  - [x] Section dropdown or text input
  - [x] Order number input (positive integer)
  - [x] Status toggle (published/draft)
  - [x] Validation messages

- [x] **Form Features** ✅
  - [x] Auto-generate slug from title
  - [x] Search parent pages as you type (debounced)
  - [x] Validate slug uniqueness (debounced API call)
  - [x] Validate parent exists
  - [x] Form state management
  - [x] Error handling

- [x] **Form Styling** ✅
  - [x] Clean form layout
  - [x] Label styling
  - [x] Input styling
  - [x] Error message styling
  - [x] Success states

#### API Endpoints Used:
- `GET /api/pages` - Search for parent pages ✅ (in use)
- `GET /api/pages/{page_id}` - Load page metadata ✅ (in use)
- `PUT /api/pages/{page_id}` - Update page metadata ✅ (in use)

#### Deliverables:
- ✅ Complete metadata editor
- ✅ Validation and error handling
- ✅ Auto-slug generation
- ✅ Comprehensive test coverage:
  - MetadataForm component: 40+ test cases
  - Slug utility: 20 test cases
  - API functions (searchPages, validateSlug): 16 test cases
  - Integration tests: 6 test cases (enhanced)
  - EditPage tests: Updated for metadata integration
- ✅ Full integration with EditPage
- ✅ Styling and UX polish

**Phase 8 Status: ✅ COMPLETE**

**Documentation**: See `client/PHASE_8_SUMMARY.md` for detailed implementation notes.

---

### Phase 9: Editing View Layout
**Goal**: Combine editor and metadata form into full editing experience

#### Tasks:
- [x] **Editing View Layout** ✅
  - [x] Toolbar with Save, Cancel, Preview, History buttons
  - [x] Metadata form at top
  - [x] Editor in middle
  - [x] Version info display
  - [x] Enhanced unsaved changes warning
  - [x] Loading states

- [x] **Editor Actions** ✅
  - [x] Save button (creates new version)
  - [x] Cancel button (discard changes, confirm if unsaved)
  - [x] Preview toggle (toggle between editor and preview)
  - [x] History button (links to version history page)

- [x] **Version History Integration** ✅
  - [x] Display current version number
  - [x] Link to view history
  - [x] Version history page component

#### API Endpoints Used:
- `GET /api/pages/{page_id}/versions` - List versions ✅ (in use)
- `GET /api/pages/{page_id}/versions/{version}` - Get specific version ✅ (API functions added)
- `GET /api/pages/{page_id}/versions/compare` - Compare versions ✅ (API functions added)
- `POST /api/pages/{page_id}/versions/{version}/restore` - Restore version ✅ (API functions added)

#### Deliverables:
- ✅ Complete editing view with enhanced layout
- ✅ Save/cancel/preview functionality
- ✅ Version history page access
- ✅ Version info display in edit header
- ✅ Enhanced unsaved changes warning with icon
- ✅ History button in actions toolbar
- ✅ Comprehensive test coverage (30+ new tests)

**Phase 9 Status: ✅ COMPLETE**

---

### Phase 10: Page Creation Flow
**Goal**: Implement "New Page" creation workflow

#### Tasks:
- [x] **New Page Modal/Page** ✅
  - [x] Choose parent page (optional) - ✅ Implemented in Phase 8
  - [x] Choose section - ✅ Implemented in Phase 8
  - [x] Enter title (slug auto-generated) - ✅ Implemented in Phase 8
  - [x] Open editor with empty content - ✅ Implemented
  - [x] Save button creates page - ✅ Implemented

- [x] **Creation Flow** ✅
  - [x] Navigate to "New Page" from header - ✅ "New Page" button added
  - [x] Fill metadata form - ✅ Implemented in Phase 8
  - [x] Write content in editor - ✅ Implemented
  - [x] Save page - ✅ Implemented
  - [x] Redirect to new page - ✅ Implemented

#### API Endpoints Used:
- `POST /api/pages` - Create new page ✅ (in use)
- `GET /api/pages` - List pages for parent selection ✅ (in use)

#### Deliverables:
- ✅ New page creation flow
- ✅ Smooth redirect after creation
- ✅ "New Page" button in header (for writers/admins)

**Phase 10 Status: ✅ COMPLETE**

---

### Phase 11: Page Delete and Archive Functionality
**Goal**: Implement page deletion and archiving with role-based permissions

#### Tasks:
- [x] **Backend Permission Checks** ✅
  - [x] Add `can_archive()` method to PageService - ✅ Implemented
  - [x] Verify `can_delete()` method works correctly - ✅ Verified
  - [x] Update `get_page` endpoint to include permission flags - ✅ Implemented

- [x] **Backend Archive Endpoints** ✅
  - [x] `POST /api/pages/<page_id>/archive` - Archive a page - ✅ Implemented
  - [x] `DELETE /api/pages/<page_id>/archive` - Unarchive a page - ✅ Implemented
  - [x] Update status validation to accept 'archived' - ✅ Implemented
  - [x] Exclude archived pages from list/search/index - ✅ Implemented

- [x] **Frontend API Functions** ✅
  - [x] `deletePage(pageId)` - Delete a page - ✅ Implemented
  - [x] `archivePage(pageId)` - Archive a page - ✅ Implemented
  - [x] `unarchivePage(pageId)` - Unarchive a page - ✅ Implemented

- [x] **Frontend UI Components** ✅
  - [x] Delete button in PageView header - ✅ Implemented
  - [x] Archive button in PageView header - ✅ Implemented
  - [x] Unarchive button in PageView header - ✅ Implemented
  - [x] Confirmation dialog component - ✅ Implemented
  - [x] Loading states during operations - ✅ Implemented

- [x] **Permission-Based Visibility** ✅
  - [x] Show delete button only when `can_delete` is true - ✅ Implemented
  - [x] Show archive button only when `can_archive` is true and page not archived - ✅ Implemented
  - [x] Show unarchive button only when `can_archive` is true and page is archived - ✅ Implemented

- [x] **Archive Behavior** ✅
  - [x] Archived pages hidden from list views - ✅ Implemented
  - [x] Archived pages hidden from search results - ✅ Implemented
  - [x] Archived pages hidden from index - ✅ Implemented
  - [x] Only admins/writers with permission can view archived pages - ✅ Implemented

#### API Endpoints Used:
- `DELETE /api/pages/<page_id>` - Delete page ✅ (existing, verified)
- `POST /api/pages/<page_id>/archive` - Archive page ✅ (new)
- `DELETE /api/pages/<page_id>/archive` - Unarchive page ✅ (new)
- `GET /api/pages/<page_id>` - Get page (now includes `can_delete` and `can_archive` flags) ✅

#### Deliverables:
- ✅ Delete page functionality with confirmation
- ✅ Archive/unarchive page functionality with confirmation
- ✅ Permission-based button visibility
- ✅ Archived pages properly hidden from normal views
- ✅ Comprehensive test coverage (12 backend tests)

**Phase 11 Status: ✅ COMPLETE**

---

### Phase 10.5: Version History & Comparison
**Goal**: Implement version history viewing and comparison

#### Tasks:
- [x] **Version History Modal/Page** ✅
  - [x] Display list of all versions - ✅ Implemented in Phase 9
  - [x] Show version number, date, author, change summary - ✅ Implemented in Phase 9
  - [x] Show diff stats (added/removed lines, char diff) - ✅ Implemented in Phase 9
  - [x] Click to view specific version - ✅ Implemented
  - [x] "Compare" button to compare versions - ✅ Implemented

- [x] **Version View** ✅
  - [x] Display specific version content
  - [x] Show version metadata
  - [x] "Restore" button (for admins/writers)
  - [x] Link back to current version

- [x] **Version Comparison** ✅
  - [x] Side-by-side comparison view
  - [x] Inline diff view (unified diff)
  - [x] Highlight additions (green) and deletions (red)
  - [x] Show diff stats summary
  - [x] Scroll synchronization
  - [x] Toggle between side-by-side and inline views

- [x] **Version Features** ✅
  - [x] Access from "History" button in editor - ✅ Implemented in Phase 9
  - [x] Access from page header (version number link) - ✅ Implemented in Phase 9
  - [ ] Keyboard shortcuts for navigation - **Optional enhancement**
  - [ ] Export version as markdown/HTML - **Optional enhancement**

#### API Endpoints Used:
- `GET /api/pages/{page_id}/versions` - List all versions ✅ (in use)
- `GET /api/pages/{page_id}/versions/{version}` - Get specific version ✅ (in use)
- `GET /api/pages/{page_id}/versions/compare?from={v1}&to={v2}` - Compare versions ✅ (in use)
- `POST /api/pages/{page_id}/versions/{version}/restore` - Restore version ✅ (in use)

#### Deliverables:
- ✅ Version history list (Phase 9)
- ✅ Version viewing (PageVersionView component)
- ✅ Version comparison (PageVersionCompare component - side-by-side and inline)
- ✅ Restore functionality

**Phase 10.5 Status: ✅ COMPLETE** (except optional enhancements)

---

### Phase 11: Responsive Design
**Goal**: Make UI work on mobile, tablet, and desktop

#### Tasks:
- [ ] **Mobile (< 768px)**
  - Collapsible sidebars (hamburger menu)
  - Stacked layout
  - Full-width content
  - Touch-friendly buttons
  - Simplified editor toolbar
  - Mobile navigation menu

- [ ] **Tablet (768px - 1024px)**
  - Sidebar can be toggled
  - Comfortable reading width maintained
  - Editor toolbar adapts
  - Responsive grid layouts

- [ ] **Desktop (> 1024px)**
  - Full three-column layout
  - All features visible
  - Optimal reading experience

- [ ] **Responsive Components**
  - Navigation tree (collapsible on mobile)
  - TOC sidebar (collapsible on mobile)
  - Editor toolbar (simplified on mobile)
  - Comments (stacked on mobile)

#### Deliverables:
- Fully responsive design
- Mobile-friendly navigation
- Touch-optimized interactions

---

### Phase 12: Accessibility
**Goal**: Ensure UI is accessible to all users

#### Tasks:
- [ ] **Keyboard Navigation**
  - Tab order is logical
  - All interactive elements keyboard accessible
  - Keyboard shortcuts documented
  - Focus management

- [ ] **Screen Reader Support**
  - ARIA labels on all interactive elements
  - Semantic HTML structure
  - Alt text for images
  - ARIA live regions for dynamic content

- [ ] **Visual Accessibility**
  - Focus indicators on all focusable elements
  - High contrast mode support
  - Color contrast ratios meet WCAG AA
  - Text resizing support

- [ ] **Testing**
  - Test with screen readers (NVDA, JAWS, VoiceOver)
  - Test keyboard-only navigation
  - Test with browser zoom (200%)
  - Test color contrast

#### Deliverables:
- WCAG 2.1 AA compliant
- Keyboard navigation working
- Screen reader tested

---

### Phase 13: Performance Optimization
**Goal**: Ensure fast, smooth user experience

#### Tasks:
- [ ] **Code Splitting**
  - Lazy load routes
  - Lazy load heavy components (editor, comments)
  - Code splitting by route

- [ ] **Caching**
  - Cache API responses (React Query or SWR)
  - Cache navigation tree
  - Cache search results
  - Use browser caching headers

- [ ] **Optimization**
  - Optimize images (lazy loading, responsive images)
  - Debounce search inputs
  - Virtualize long lists (comments, search results)
  - Memoize expensive computations

- [ ] **Performance Monitoring**
  - Measure page load times
  - Measure time to interactive
  - Monitor API call performance
  - Use React DevTools Profiler

#### Deliverables:
- Fast page loads (< 2s initial)
- Smooth interactions (60fps)
- Optimized API usage

---

### Phase 14: Polish & Enhancements
**Goal**: Add polish and user experience enhancements

#### Tasks:
- [ ] **Animations & Transitions**
  - Smooth page transitions
  - Loading skeletons
  - Smooth scroll animations
  - Hover effects
  - Button press animations

- [ ] **Error Handling**
  - User-friendly error messages
  - Retry mechanisms
  - Offline detection
  - Network error handling

- [ ] **User Feedback**
  - Success notifications
  - Error notifications
  - Loading indicators
  - Progress indicators

- [ ] **Theme Support**
  - Light/dark mode toggle
  - Respect system preferences
  - Persist theme choice

- [ ] **Additional Features**
  - Print stylesheet
  - Share page functionality
  - Copy link to page
  - Export page as PDF (optional)

#### Deliverables:
- Polished, professional UI
- Smooth animations
- Comprehensive error handling
- Theme support

---

## Technical Stack Recommendations

### Framework
- **React 18+** (recommended for Tiptap integration and ecosystem)
- Alternative: Vue 3 or SvelteKit

### Editor
- **Tiptap** (`@tiptap/react`) - Already specified in design doc
- Required extensions:
  - `@tiptap/starter-kit` (base functionality)
  - `@tiptap/extension-link` (links)
  - `@tiptap/extension-image` (images)
  - `@tiptap/extension-table` (tables)
  - `@tiptap/extension-code-block` (code blocks)
  - `@tiptap/extension-markdown` (markdown import/export)

### Routing
- **React Router v6** (if using React)
- Alternative: Vue Router or SvelteKit routing

### State Management
- **React Query / TanStack Query** (for server state)
- **Zustand** or **Context API** (for client state)
- Alternative: Redux Toolkit, Pinia (Vue)

### Styling
- **Tailwind CSS** (recommended for rapid development)
- Alternative: CSS Modules, styled-components, or SCSS

### HTTP Client
- **Axios** (recommended)
- Alternative: Fetch API wrapper

### Code Highlighting
- **Prism.js** or **highlight.js** (for code blocks)

### Build Tool
- **Vite** (already configured)

---

## API Integration Notes

### Authentication
- JWT tokens stored in localStorage or httpOnly cookies
- Token refresh mechanism
- Handle 401 errors (redirect to login)

### Error Handling
- Centralized error handling
- User-friendly error messages
- Retry logic for network errors
- Offline detection

### API Service Structure
```
src/
  services/
    api/
      client.js          # Axios instance with interceptors
      pages.js           # Page API calls
      comments.js        # Comment API calls
      search.js          # Search API calls
      navigation.js      # Navigation API calls
      upload.js          # Upload API calls
      auth.js            # Auth integration
```

---

## Component Structure

### Recommended Component Organization
```
src/
  components/
    layout/
      Header.jsx
      Footer.jsx
      Layout.jsx
      Sidebar.jsx
    navigation/
      NavTree.jsx
      Breadcrumbs.jsx
      PrevNext.jsx
    content/
      PageContent.jsx
      TableOfContents.jsx
      Backlinks.jsx
    comments/
      CommentsList.jsx
      CommentItem.jsx
      CommentForm.jsx
    editor/
      Editor.jsx
      EditorToolbar.jsx
      MetadataForm.jsx
    search/
      SearchBar.jsx
      SearchResults.jsx
      IndexView.jsx
    common/
      Button.jsx
      Input.jsx
      Modal.jsx
      Loading.jsx
  pages/
    HomePage.jsx
    PageView.jsx
    EditPage.jsx
    SearchPage.jsx
    IndexPage.jsx
  services/
    api/
      ...
  utils/
    markdown.js
    formatting.js
    validation.js
```

---

## Testing Strategy

### Unit Tests
- Component tests (React Testing Library)
- Utility function tests
- API service tests (mocked)
- **Status**: ✅ Comprehensive coverage (550+ passing tests across 35 test files)
  - All components fully tested
  - Edge cases covered
  - Error scenarios handled
  - Integration flows tested
  - Phase 5: 38+ new tests (CommentsList, CommentItem, CommentForm, comments API)
  - Phase 8: 86+ new tests (MetadataForm, slug utility, API functions)
  - Auth system: 90+ new tests (AuthContext, auth API, sign-in page, header auth)
  - Phase 9: 30+ new tests (PageHistoryPage, version API functions, EditPage version features)

### Integration Tests
- User flows (create page, edit page, comment)
- Navigation flows
- Search flows
- Metadata editing flows
- **Status**: ✅ Core flows tested (11+ integration tests)
  - Page creation/editing flows
  - Metadata editing flows
  - Authentication flows
  - Comments flows (create, edit, delete, reply)

### E2E Tests ✅ (Implemented)
- **Playwright** - Full browser testing
- Critical user journeys:
  - Page viewing with syntax highlighting
  - Navigation (breadcrumbs, tree, prev/next)
  - Table of Contents scrolling and highlighting
  - Backlinks navigation
  - Link processing (internal vs external)
- **Status**: ✅ E2E test suite implemented (20+ tests)
- **Run**: `npm run test:e2e` from `client/` directory
- **Documentation**: See `client/e2e/README.md`

---

## Implementation Priority

### MVP (Minimum Viable Product)
1. Phase 1: Foundation & Setup
2. Phase 2: Reading View - Core Components
3. Phase 3: Navigation Tree
4. Phase 4: Table of Contents & Backlinks
5. Phase 5: Comments System
6. Phase 7: WYSIWYG Editor Integration (basic)
7. Phase 8: Page Metadata Editor
8. Phase 9: Editing View Layout
9. Phase 10: Page Creation Flow

### Enhanced Features
- Phase 6: Search Interface
- Phase 11: Responsive Design
- Phase 12: Accessibility

### Polish
- Phase 13: Performance Optimization
- Phase 14: Polish & Enhancements

---

## Next Steps

### Immediate Next Steps

1. **Phase 11: Responsive Design** (Next Priority)
   - Mobile (< 768px) layout
   - Tablet (768px - 1024px) layout
   - Desktop (> 1024px) layout
   - Responsive components

2. **Phase 12: Accessibility**
   - Keyboard navigation
   - Screen reader support
   - Visual accessibility

3. **Phase 13: Performance Optimization**
   - Code splitting
   - Caching strategies
   - Optimization techniques

4. **Phase 14: Polish & Enhancements**
   - Animations & transitions
   - Error handling improvements
   - Theme support

### Completed Phases

- ✅ **Phase 1: Foundation & Setup** - Complete
- ✅ **Phase 2: Reading View - Core Components** - Complete (including Edit button)
- ✅ **Phase 3: Navigation Tree (Left Sidebar)** - Complete
- ✅ **Phase 4: Table of Contents & Backlinks (Right Sidebar)** - Complete
- ✅ **Phase 5: Comments System** - Complete (except optional pagination)
- ✅ **Phase 6: Search Interface** - Complete (except optional enhancements)
- ✅ **Phase 7: WYSIWYG Editor Integration** - Complete (except optional enhancements)
- ✅ **Phase 8: Page Metadata Editor** - Complete
- ✅ **Phase 9: Editing View Layout** - Complete
- ✅ **Phase 10: Page Creation Flow** - Complete
- ✅ **Phase 10.5: Version History & Comparison** - Complete (except optional enhancements)

**Test Coverage**: 560+ passing tests across 35 test files, comprehensive edge case coverage

---

## Notes

- Backend API is complete and ready to consume
- All API endpoints are documented in `docs/api/wiki-api.md`
- Design specifications are in `docs/wiki-user-interface.md`
- This guide assumes React, but can be adapted for other frameworks
- Tiptap is the specified editor (design doc requirement)
- Focus on MVP first, then enhance with additional features

## Phase 5 Implementation Summary

Phase 5: Comments System has been completed with comprehensive test coverage.

**Key Achievements**:
- ✅ Threaded comments system (up to 5 levels deep)
- ✅ CommentsList, CommentItem, and CommentForm components
- ✅ Full CRUD operations (create, read, update, delete)
- ✅ Reply functionality with depth limits
- ✅ Edit/delete own comments
- ✅ Recommendation badge for player suggestions
- ✅ Collapsible reply threads
- ✅ Relative and absolute timestamps
- ✅ 38+ new test cases
- ✅ Full integration with PageView component
- ✅ Comprehensive error handling and edge cases

## Phase 7 Implementation Summary

Phase 7: WYSIWYG Editor Integration has been completed with comprehensive test coverage.

**Key Achievements**:
- ✅ Tiptap-based rich text editor with full formatting capabilities
- ✅ Editor component with markdown import/export
- ✅ EditorToolbar component with all formatting tools (headings, bold, italic, code, lists, links, images, tables)
- ✅ Code blocks with syntax highlighting
- ✅ Undo/redo functionality
- ✅ EditPage component with auto-save drafts to localStorage
- ✅ 69+ new test cases (Editor: 14, EditorToolbar: 33, EditPage: 22)
- ✅ Full integration with page creation and editing flows
- ✅ Comprehensive error handling and edge cases

## Phase 8 Implementation Summary

Phase 8: Page Metadata Editor has been completed with comprehensive test coverage. See `client/PHASE_8_SUMMARY.md` for detailed implementation notes.

**Key Achievements**:
- ✅ Complete metadata editing form with all fields
- ✅ Real-time slug validation with debouncing
- ✅ Parent page search with debouncing
- ✅ Auto-slug generation from title
- ✅ 86+ new test cases
- ✅ Full integration with EditPage component
- ✅ Comprehensive error handling and edge cases

## Phase 9 Implementation Summary

Phase 9: Editing View Layout has been completed with comprehensive test coverage.

**Key Achievements**:
- ✅ Enhanced EditPage layout with version info display
- ✅ Version history page component (PageHistoryPage)
- ✅ Version API integration (fetchVersionHistory, fetchVersion, compareVersions, restoreVersion)
- ✅ Enhanced unsaved changes warning with icon
- ✅ History button in actions toolbar
- ✅ Version info display in edit header (current version number)
- ✅ Links to version history page
- ✅ 30+ new test cases:
  - PageHistoryPage: 18 tests
  - Version API functions: 6 tests
  - EditPage version features: 6 tests
- ✅ Full integration with existing EditPage functionality
- ✅ Comprehensive error handling and edge cases

**New Components**:
- `PageHistoryPage` - Displays version history list with metadata, diff stats, and navigation links

**New API Functions**:
- `fetchVersionHistory(pageId)` - Get all versions for a page
- `useVersionHistory(pageId)` - React Query hook for version history
- `fetchVersion(pageId, version)` - Get specific version
- `useVersion(pageId, version)` - React Query hook for specific version
- `compareVersions(pageId, version1, version2)` - Compare two versions
- `restoreVersion(pageId, version)` - Restore a version

**Files Created/Modified**:
- `client/src/pages/PageHistoryPage.jsx` - New version history page
- `client/src/pages/EditPage.jsx` - Enhanced with version info and history links
- `client/src/services/api/pages.js` - Added version API functions
- `client/src/App.jsx` - Added history route
- `client/src/styles.css` - Added styles for Phase 9 components
- `client/src/test/pages/PageHistoryPage.test.jsx` - New test file (18 tests)
- `client/src/test/services/pages-api.test.js` - Added version API tests (6 tests)
- `client/src/test/pages/EditPage.test.jsx` - Added version feature tests (6 tests)

## Phase 6 Implementation Summary

Phase 6: Search Interface has been completed with all optional enhancements.

**Key Achievements**:
- ✅ Global search bar in header with keyboard shortcut (Ctrl+K / Cmd+K)
- ✅ Search results page with highlighting and relevance scores
- ✅ Alphabetical index view with letter navigation and section filtering
- ✅ Search API integration (`/api/search` and `/api/index` endpoints)
- ✅ Search term highlighting in results
- ✅ **Recent searches dropdown** (localStorage, max 10 items)
- ✅ **Search suggestions as you type** (debounced, 300ms)
- ✅ **Clear button** for search input
- ✅ **Pagination** for search results (20 results per page)
- ✅ **Page count per letter** in index view
- ✅ Comprehensive test coverage

**New Components**:
- `SearchPage` - Full search results page with query handling, suggestions, and pagination
- `IndexPage` - Alphabetical index with filters, search, and page counts

**New API Functions**:
- `searchPages(query, options)` - Search pages by query (supports limit and offset)
- `useSearch(query, options)` - React Query hook for search
- `fetchIndex()` - Get master index
- `useIndex()` - React Query hook for index

**Files Created/Modified**:
- `client/src/services/api/search.js` - Search API module with pagination support
- `client/src/pages/SearchPage.jsx` - Enhanced with suggestions, clear button, and pagination
- `client/src/pages/IndexPage.jsx` - Enhanced with page counts per letter
- `client/src/components/layout/Header.jsx` - Enhanced with recent searches dropdown and clear button
- `client/src/styles.css` - Added styles for search enhancements
- `client/src/test/pages/SearchPage.test.jsx` - Updated tests (7 tests)
- `client/src/test/pages/IndexPage.test.jsx` - Updated tests (6 tests)
- `services/wiki/app/routes/search_routes.py` - Added pagination support (offset parameter)

## Phase 10 Implementation Summary

Phase 10: Page Creation Flow has been completed.

**Key Achievements**:
- ✅ "New Page" button in header (visible to writers/admins)
- ✅ Complete page creation workflow
- ✅ Smooth redirect after creation
- ✅ All metadata fields available (from Phase 8)
- ✅ Auto-save drafts for new pages

**Files Modified**:
- `client/src/components/layout/Header.jsx` - Added "New Page" button
- `client/src/styles.css` - Added styles for new page button

## Phase 10.5 Implementation Summary

Phase 10.5: Version History & Comparison has been completed.

**Key Achievements**:
- ✅ Version viewing page (PageVersionView)
- ✅ Version comparison page (PageVersionCompare)
- ✅ Side-by-side and inline diff views
- ✅ Restore version functionality
- ✅ Scroll synchronization for side-by-side view
- ✅ Diff stats display
- ✅ Permission-based restore button (writers/admins)

**New Components**:
- `PageVersionView` - Displays specific version content with restore option
- `PageVersionCompare` - Compares two versions side-by-side or inline

**Files Created/Modified**:
- `client/src/pages/PageVersionView.jsx` - New version view page
- `client/src/pages/PageVersionCompare.jsx` - New version comparison page
- `client/src/App.jsx` - Added version view and compare routes
- `client/src/styles.css` - Added version view and compare styles

---

## Phase 11 Implementation Summary

Phase 11: Page Delete and Archive Functionality has been completed.

**Key Achievements**:
- ✅ Delete page functionality with role-based permissions
- ✅ Archive/unarchive page functionality with role-based permissions
- ✅ Confirmation dialogs for all destructive actions
- ✅ Permission flags (`can_delete`, `can_archive`) in API responses
- ✅ Archived pages hidden from normal views (list, search, index)
- ✅ Comprehensive test coverage (12 backend tests, frontend tests)

**Permission Model**:
- **Admins**: Can delete or archive any page
- **Writers**: Can delete or archive only their own pages
- **Viewers/Players**: No delete or archive permissions

**Archive Behavior**:
- Archived pages are hidden from:
  - List views (`/api/pages`)
  - Search results (`/api/search`)
  - Index views (`/api/index`)
- Archived pages can be viewed by:
  - Admins (any archived page)
  - Writers (only their own archived pages)
- Archived pages can be restored via unarchive action

**New Components**:
- `DeleteArchiveDialog` - Reusable confirmation dialog for delete/archive/unarchive actions
  - Different messaging for each action type
  - Warning for delete (mentions orphaned children)
  - Loading states during operations

**New API Endpoints**:
- `DELETE /api/pages/<page_id>` - Delete a page (existing, verified)
- `POST /api/pages/<page_id>/archive` - Archive a page
- `DELETE /api/pages/<page_id>/archive` - Unarchive a page

**API Response Updates**:
- `GET /api/pages/<page_id>` now includes:
  - `can_delete` (boolean) - Whether user can delete this page
  - `can_archive` (boolean) - Whether user can archive this page

**New API Functions**:
- `deletePage(pageId)` - Delete a page
- `archivePage(pageId)` - Archive a page
- `unarchivePage(pageId)` - Unarchive a page

**Files Created/Modified**:
- `client/src/components/page/DeleteArchiveDialog.jsx` - New confirmation dialog component
- `client/src/components/page/DeleteArchiveDialog.css` - Dialog styles
- `client/src/pages/PageView.jsx` - Added delete/archive buttons and dialogs
- `client/src/services/api/pages.js` - Added delete/archive API functions
- `client/src/styles.css` - Added styles for action buttons
- `services/wiki/app/routes/page_routes.py` - Added archive/unarchive endpoints
- `services/wiki/app/services/page_service.py` - Added `can_archive()` method
- `services/wiki/app/services/search_index_service.py` - Exclude archived pages from search
- `services/wiki/tests/test_api/test_page_routes.py` - Added 9 new tests for archive functionality

**Backend Tests Added**:
- `test_archive_page_success` - Successfully archive a page
- `test_archive_page_requires_auth` - Archive requires authentication
- `test_archive_page_insufficient_permissions` - Writers cannot archive others' pages
- `test_admin_can_archive_any_page` - Admins can archive any page
- `test_unarchive_page_success` - Successfully unarchive a page
- `test_archive_already_archived_page` - Error when archiving already archived page
- `test_unarchive_not_archived_page` - Error when unarchiving non-archived page
- `test_get_page_includes_permission_flags` - API includes can_delete and can_archive flags
- `test_archived_page_hidden_from_list` - Archived pages excluded from list views

**Phase 11 Status: ✅ COMPLETE**
