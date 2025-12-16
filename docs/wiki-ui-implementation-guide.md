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

### 🧩 Frontend UI (In Progress)

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
  - [ ] Edit button (for writers/admins) - **TODO** (requires auth integration)

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

**Phase 2 Status: ✅ COMPLETE** (except Edit button which requires auth integration)

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
  - [ ] Icons for pages vs sections - **TODO** (optional enhancement)

- [x] **Tree Search** ✅
  - [x] Search/filter within tree
  - [x] Auto-expand matching branches
  - [x] Filter non-matching branches

- [x] **Tree Features** ✅
  - [x] Remember expanded state (localStorage)
  - [x] Draft badge indicator
  - [ ] Show page count per section - **TODO** (optional enhancement)
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
  - [ ] Icons for pages vs sections - **TODO** (optional enhancement)

- [x] **Tree Search** ✅
  - [x] Search/filter within tree
  - [x] Auto-expand matching branches
  - [x] Filter non-matching branches

- [x] **Tree Features** ✅
  - [x] Remember expanded state (localStorage)
  - [x] Draft badge indicator
  - [ ] Show page count per section - **TODO** (optional enhancement)
  - [ ] Lazy load children - **TODO** (not needed yet, performance is good)

#### API Endpoints Used:
- `GET /api/navigation` - Get hierarchical structure ✅ (in use)

#### Deliverables:
- ✅ Functional navigation tree
- ✅ Search within tree
- ✅ Smooth expand/collapse (CSS transitions)
- ✅ Expanded state persistence
- ✅ Current page highlighting

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
  - [ ] Collapsible if page is short - **TODO** (optional enhancement)

- [x] **Backlinks Component** ✅
  - [x] Display pages that link to current page
  - [ ] Show context snippet (where link appears) - **TODO** (optional enhancement)
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
- [ ] **Comments List Component**
  - Display threaded comments (max 5 levels deep)
  - Visual indentation for thread depth
  - User avatars/names
  - Timestamps (relative and absolute)
  - Collapsible threads
  - Pagination for long threads

- [ ] **Comment Form Component**
  - Text area for new comment
  - Reply button on each comment (disabled at max depth)
  - "Recommend update" checkbox (for players)
  - Submit button
  - Loading states
  - Error handling

- [ ] **Comment Actions**
  - Edit own comments (inline editing)
  - Delete own comments (with confirmation)
  - Mark as recommendation (special styling)
  - Visual indicator for thread depth

- [ ] **Comment Styling**
  - Light background for comments section
  - Clear separation between threads
  - Highlight recommendations
  - Responsive layout

#### API Endpoints Used:
- `GET /api/pages/{page_id}/comments` - List comments
- `POST /api/pages/{page_id}/comments` - Create comment
- `PUT /api/comments/{comment_id}` - Update comment
- `DELETE /api/comments/{comment_id}` - Delete comment

#### Deliverables:
- Fully functional threaded comments
- Reply, edit, delete functionality
- Recommendation styling
- Pagination

---

### Phase 6: Search Interface
**Goal**: Implement global search functionality

#### Tasks:
- [ ] **Search Bar Component**
  - Search input in header
  - Dropdown with recent searches (localStorage)
  - Search suggestions as you type (debounced)
  - Clear button
  - Keyboard shortcuts (Ctrl+K / Cmd+K)

- [ ] **Search Results Page**
  - Display search results
  - Show: title, snippet, section, relevance score
  - Highlight search terms
  - Click to navigate to page
  - Pagination
  - "No results" state

- [ ] **Index View**
  - Alphabetical listing of all pages
  - Filter by section
  - Click letter to jump to section
  - Show page count per letter
  - Search within index

#### API Endpoints Used:
- `GET /api/search?q={query}` - Full-text search
- `GET /api/search/index` - Get index entries
- `GET /api/pages` - List all pages for index

#### Deliverables:
- Global search bar
- Search results page
- Alphabetical index view
- Search suggestions

---

### Phase 7: WYSIWYG Editor Integration
**Goal**: Integrate Tiptap editor for page editing

#### Tasks:
- [ ] **Install Tiptap Dependencies**
  - Install `@tiptap/react` and core packages
  - Install extensions (bold, italic, lists, links, images, tables, code)
  - Install markdown extension for import/export

- [ ] **Editor Component**
  - Initialize Tiptap editor
  - Configure toolbar with all required buttons
  - Format dropdown (H1-H6, Paragraph)
  - Bold, Italic, Underline buttons
  - Bullet list, Numbered list buttons
  - Link button (with internal page search dialog)
  - Image upload/insert button
  - Code block button
  - Table button
  - Undo/Redo buttons

- [ ] **Editor Features**
  - Load markdown content into editor
  - Export editor content to markdown
  - Real-time preview toggle
  - Auto-save drafts (localStorage + API)
  - Link insertion dialog with page search
  - Image upload with preview
  - Table editor (visual grid)
  - Keyboard shortcuts

- [ ] **Editor Styling**
  - Clean white background
  - Comfortable padding
  - Toolbar styling
  - Content area styling
  - Focus states

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Load page for editing
- `PUT /api/pages/{page_id}` - Save page updates
- `POST /api/pages` - Create new page
- `POST /api/upload/images` - Upload images

#### Deliverables:
- Fully functional Tiptap editor
- All formatting tools working
- Link and image insertion
- Auto-save drafts

---

### Phase 8: Page Metadata Editor
**Goal**: Implement form for editing page metadata

#### Tasks:
- [ ] **Metadata Form Component**
  - Title input (required)
  - Slug input (auto-generated from title, editable)
  - Parent page dropdown (with search)
  - Section dropdown or text input
  - Order number input (positive integer)
  - Status toggle (published/draft)
  - Validation messages

- [ ] **Form Features**
  - Auto-generate slug from title
  - Search parent pages as you type
  - Validate slug uniqueness (debounced API call)
  - Validate parent exists
  - Form state management
  - Error handling

- [ ] **Form Styling**
  - Clean form layout
  - Label styling
  - Input styling
  - Error message styling
  - Success states

#### API Endpoints Used:
- `GET /api/pages` - Search for parent pages
- `GET /api/pages/{page_id}` - Load page metadata
- `PUT /api/pages/{page_id}` - Update page metadata

#### Deliverables:
- Complete metadata editor
- Validation and error handling
- Auto-slug generation

---

### Phase 9: Editing View Layout
**Goal**: Combine editor and metadata form into full editing experience

#### Tasks:
- [ ] **Editing View Layout**
  - Toolbar with Save, Cancel, Preview, History buttons
  - Metadata form at top
  - Editor in middle
  - Version info display
  - Unsaved changes warning
  - Loading states

- [ ] **Editor Actions**
  - Save button (creates new version)
  - Cancel button (discard changes, confirm if unsaved)
  - Preview toggle (side-by-side or toggle)
  - History button (opens version history modal)

- [ ] **Version History Integration**
  - Display current version number
  - Link to view history
  - Show "View History" modal/page

#### API Endpoints Used:
- `GET /api/pages/{page_id}/versions` - List versions
- `GET /api/pages/{page_id}/versions/{version}` - Get specific version
- `GET /api/pages/{page_id}/versions/compare` - Compare versions

#### Deliverables:
- Complete editing view
- Save/cancel/preview functionality
- Version history access

---

### Phase 10: Page Creation Flow
**Goal**: Implement "New Page" creation workflow

#### Tasks:
- [ ] **New Page Modal/Page**
  - Choose parent page (optional)
  - Choose section
  - Enter title (slug auto-generated)
  - Open editor with empty content
  - Save button creates page

- [ ] **Creation Flow**
  - Navigate to "New Page" from header or tree
  - Fill metadata form
  - Write content in editor
  - Save page
  - Redirect to new page

#### API Endpoints Used:
- `POST /api/pages` - Create new page
- `GET /api/pages` - List pages for parent selection

#### Deliverables:
- New page creation flow
- Smooth redirect after creation

---

### Phase 10.5: Version History & Comparison
**Goal**: Implement version history viewing and comparison

#### Tasks:
- [ ] **Version History Modal/Page**
  - Display list of all versions
  - Show version number, date, author, change summary
  - Show diff stats (added/removed lines, char diff)
  - Click to view specific version
  - "Compare" button to compare versions

- [ ] **Version View**
  - Display specific version content
  - Show version metadata
  - "Restore" button (for admins/writers)
  - Link back to current version

- [ ] **Version Comparison**
  - Side-by-side comparison view
  - Inline diff view (unified diff)
  - Highlight additions (green) and deletions (red)
  - Show diff stats summary
  - Scroll synchronization
  - Toggle between side-by-side and inline views

- [ ] **Version Features**
  - Access from "History" button in editor
  - Access from page header (version number link)
  - Keyboard shortcuts for navigation
  - Export version as markdown/HTML

#### API Endpoints Used:
- `GET /api/pages/{page_id}/versions` - List all versions
- `GET /api/pages/{page_id}/versions/{version}` - Get specific version
- `GET /api/pages/{page_id}/versions/compare?version1={v1}&version2={v2}` - Compare versions

#### Deliverables:
- Version history list
- Version viewing
- Version comparison (side-by-side and inline)
- Restore functionality

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
- **Status**: ✅ Comprehensive coverage (112+ tests)

### Integration Tests
- User flows (create page, edit page, comment)
- Navigation flows
- Search flows
- **Status**: ✅ Core flows tested

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
5. Phase 7: WYSIWYG Editor Integration (basic)
6. Phase 8: Page Metadata Editor
7. Phase 9: Editing View Layout
8. Phase 10: Page Creation Flow

### Enhanced Features
- Phase 5: Comments System
- Phase 6: Search Interface
- Phase 11: Responsive Design
- Phase 12: Accessibility

### Polish
- Phase 13: Performance Optimization
- Phase 14: Polish & Enhancements

---

## Next Steps

### Immediate Next Steps

1. **Phase 3: Navigation Tree (Left Sidebar)**
   - Implement hierarchical page navigation tree
   - Expandable/collapsible nodes
   - Tree search/filter
   - Highlight current page
   - Remember expanded state (localStorage)

2. **Phase 4: Table of Contents & Backlinks (Right Sidebar)**
   - Auto-generate TOC from page headings
   - Scroll-to-section functionality
   - Active section highlighting while scrolling
   - Display backlinks (pages linking to current page)

3. **Phase 5: Comments System**
   - Threaded comments display
   - Comment form (create, reply, edit, delete)
   - Recommendation styling for player suggestions

4. **Phase 6: Search Interface**
   - Global search bar in header
   - Search results page
   - Alphabetical index view

5. **Phase 7: WYSIWYG Editor Integration**
   - Integrate Tiptap editor
   - Page editing interface
   - Auto-save drafts
   - Preview mode

### Completed Phases

- ✅ **Phase 1: Foundation & Setup** - Complete
- ✅ **Phase 2: Reading View - Core Components** - Complete (except Edit button, requires auth)

---

## Notes

- Backend API is complete and ready to consume
- All API endpoints are documented in `docs/api/wiki-api.md`
- Design specifications are in `docs/wiki-user-interface.md`
- This guide assumes React, but can be adapted for other frameworks
- Tiptap is the specified editor (design doc requirement)
- Focus on MVP first, then enhance with additional features
