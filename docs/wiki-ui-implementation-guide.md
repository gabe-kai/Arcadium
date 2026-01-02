# Wiki UI Implementation Guide

This guide outlines the implementation status and details for the Wiki User Interface. The backend API is complete and ready to consume.

## Current Status

### ✅ Backend API (Complete)
- All API endpoints implemented and tested (560+ tests passing)
- Page CRUD operations
- Comments system with threading
- Search and indexing
- Navigation and hierarchy
- Version history
- File uploads
- Admin dashboard endpoints
- Service status endpoints

### ✅ Frontend UI (Phases 1-11, 15 Complete)
**Test Coverage**: 523+ passing unit/integration tests across 35 test files, 32+ E2E tests
**Backend Test Coverage**: 560+ passing tests across 50+ test files
**Total Project Coverage**: 1,115+ tests across 89+ test files

---

## Table of Contents

1. [Completed Phases](#completed-phases)
2. [Implementation Details](#implementation-details)
3. [Technical Stack](#technical-stack)
4. [Component Structure](#component-structure)
5. [Testing Strategy](#testing-strategy)
6. [Future Enhancements](#future-enhancements)

---

## Completed Phases

### ✅ Phase 1: Foundation & Setup
- React + Vite client bootstrapped in `client/`
- Project structure (`components`, `pages`, `services`, `utils`, `test`)
- React Router configured with core routes
- Base layout components (header, footer, layout, sidebar)
- Initial styling for modern, book-like reading shell
- Axios API client with `VITE_WIKI_API_BASE_URL`
- Testing infrastructure (Vitest + React Testing Library)
- CORS configured
- React Query integration
- Auth context (JWT token storage)
- E2E Testing (Playwright)

### ✅ Phase 2: Reading View - Core Components
- **PageView component** - Full reading experience with content rendering, metadata display
- **Edit button** - Shown for writers/admins with edit permissions
- **Delete/Archive buttons** - Shown based on permissions
- **Breadcrumb Navigation** - Component with API integration
- **Previous/Next Navigation** - Component with API integration
- **Enhanced Content Styling**:
  - Syntax highlighting (Prism.js with multiple languages)
  - Responsive image handling
  - Styled tables (striped rows, hover effects)
  - Enhanced blockquotes
  - Internal vs external link distinction
- **API Integration**: `usePage`, `useBreadcrumb`, `usePageNavigation` hooks

### ✅ Phase 3: Navigation Tree (Left Sidebar)
- **NavigationTree component** - Hierarchical page navigation
- **Tree Features**:
  - Expandable/collapsible tree nodes with animations
  - Highlights current page
  - Auto-expands path to current page
  - Persists expanded state in localStorage
  - Draft badge indicator
  - Hover effects and active state highlighting
  - Page count per section
- **Section View Toggle** ✅ (Major Feature):
  - Toggle between hierarchical view and section grouping
  - Section grouping displays pages grouped by section
  - "No Section" grouping for pages without section (appears at top)
  - Folder icons for sections, document icons for pages
  - Section view is default when page loads
  - Preference persisted in localStorage
  - **Default Section States**: "Regression-Testing" section is collapsed by default (all other sections expanded by default)
  - Sections auto-expand when navigating to a page within them
- **Tree Search** - Search/filter within tree with auto-expand matching branches
- **API Integration**: `useNavigationTree` hook with 5-minute cache

### ✅ Phase 4: Table of Contents & Backlinks (Right Sidebar)
- **TableOfContents component** - Auto-generated from page headings (H2-H6)
  - Click to scroll to section (smooth scroll)
  - Highlight current section while scrolling
  - Indentation for nested headings
  - Active section highlighting
  - **Sticky positioning**: TOC follows viewport as user scrolls page content
    - TOC container uses CSS `position: sticky` with `top: 1.5rem`
    - Container has `max-height: calc(100vh - 3rem)` to stay within viewport
    - TOC list is scrollable when content exceeds viewport height
    - Auto-scrolls TOC list to keep active section visible when TOC is taller than viewport
    - Smooth scroll behavior with 20px padding from top/bottom
    - Custom scrollbar styling for better UX
  - Collapsible for pages with < 5 TOC items
- **Backlinks component** - Displays pages that link to current page
  - Shows backlink count
  - Click to navigate to linking page
  - Styled list with hover effects
- **Integration**: Both components integrated into PageView right sidebar

### ✅ Phase 5: Comments System
- **CommentsList component** - Displays all comments with threading
- **CommentItem component** - Single comment with nested replies (up to 5 levels)
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
  - Pagination (10 comments per page with navigation)
- **API Integration**: `useComments`, `useCreateComment`, `useUpdateComment`, `useDeleteComment` hooks

### ✅ Phase 6: Search Interface
- **Search Bar Component** - In header with keyboard shortcuts (Ctrl+K / Cmd+K)
  - Recent searches dropdown (localStorage, max 10 items)
  - Search suggestions as you type (debounced, 300ms)
  - Clear button
- **Search Results Page** - Full search results with:
  - Title, snippet, section, relevance score
  - Search term highlighting
  - Pagination (20 results per page)
  - "No results" state
- **Index View** - Alphabetical listing:
  - Filter by section
  - Click letter to jump to section
  - Search within index
  - Page count per letter
- **API Integration**: `useSearch`, `useIndex` hooks

### ✅ Phase 7: WYSIWYG Editor Integration
- **Editor Component** - Tiptap-based rich text editor
  - Markdown import/export
  - All formatting tools (headings, bold, italic, code, lists, links, images, tables)
  - Code blocks with syntax highlighting
  - Undo/redo functionality
  - Real-time preview toggle
- **EditorToolbar Component** - Full formatting toolbar
  - Format dropdown (H1-H6, Paragraph)
  - Text formatting buttons
  - List buttons
  - Link and image insertion
  - Code block and table insertion
  - Two-row toolbar (table controls appear when cursor is in table)
- **EditPage Component** - Full editing interface
  - Editor integration
  - Auto-save drafts to localStorage
  - Save/create page functionality
  - **Save Navigation**: After successful save, navigates back to view mode (not staying in editor)

### ✅ Phase 8: Page Metadata Editor
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
- **Integration**: Fully integrated into EditPage component

### ✅ Phase 9: Editing View Layout
- **Editing View Layout**:
  - Toolbar with Save, Cancel, Preview, History buttons
  - Metadata form at top
  - Editor in middle
  - Version info display
  - Enhanced unsaved changes warning
  - Loading states
- **Version History Integration**:
  - Display current version number
  - Link to view history
  - Version history page component (PageHistoryPage)
- **Editor Actions**:
  - Save button (creates new version, navigates to view mode)
  - Cancel button (discard changes, confirm if unsaved)
  - Preview toggle (toggle between editor and preview)
  - History button (links to version history page)

### ✅ Phase 10: Page Creation Flow
- **New Page Modal/Page**:
  - Choose parent page (optional)
  - Choose section
  - Enter title (slug auto-generated)
  - Open editor with empty content
  - Save button creates page
- **Creation Flow**:
  - Navigate to "New Page" from header ("New Page" button)
  - Fill metadata form
  - Write content in editor
  - Save page
  - Redirect to new page (view mode)

### ✅ Phase 10.5: Version History & Comparison
- **Version History Modal/Page**:
  - Display list of all versions
  - Show version number, date, author, change summary
  - Show diff stats (added/removed lines, char diff)
  - Click to view specific version
  - "Compare" button to compare versions
- **Version View**:
  - Display specific version content
  - Show version metadata
  - "Restore" button (for admins/writers)
  - Link back to current version
- **Version Comparison**:
  - Side-by-side comparison view
  - Inline diff view (unified diff)
  - Highlight additions (green) and deletions (red)
  - Show diff stats summary
  - Scroll synchronization
  - Toggle between side-by-side and inline views

### ✅ Phase 11: Page Delete and Archive Functionality
- **Backend Permission Checks**:
  - `can_archive()` method in PageService
  - `can_delete()` method verified
  - Permission flags in API responses
- **Backend Archive Endpoints**:
  - `POST /api/pages/<page_id>/archive` - Archive a page
  - `DELETE /api/pages/<page_id>/archive` - Unarchive a page
  - Archived pages excluded from list/search/index
- **Frontend UI Components**:
  - Delete button in PageView header
  - Archive button in PageView header
  - Unarchive button in PageView header
  - Confirmation dialog component (DeleteArchiveDialog)
  - Loading states during operations
- **Permission-Based Visibility**:
  - Show delete button only when `can_delete` is true
  - Show archive button only when `can_archive` is true and page not archived
  - Show unarchive button only when `can_archive` is true and page is archived

### ✅ Phase 15: Polish & Enhancements
- **Animations & Transitions**:
  - Smooth page transitions
  - Loading skeletons
  - Smooth scroll animations
  - Hover effects
  - Button press animations
- **Error Handling**:
  - User-friendly error messages
  - Retry mechanisms
  - Offline detection
  - Network error handling
- **User Feedback**:
  - Success notifications (NotificationProvider)
  - Error notifications
  - Loading indicators
  - Progress indicators
- **Theme Support**:
  - Light/dark mode toggle (ThemeToggle component)
  - Respect system preferences
  - Persist theme choice
  - Header and all components adapt to theme
- **Additional Features**:
  - Print stylesheet
  - Share page functionality (ShareButton component)
  - Copy link to page
  - Service status indicator (ServiceStatusIndicator component)
  - Profile page (ProfilePage component)
  - Service management page (ServiceManagementPage component)

---

## Implementation Details

### Navigation Tree Enhancements

#### Section View Toggle

**Feature**: Toggle between hierarchical tree view and section grouping view

**Implementation**:
- Toggle checkbox in navigation tree controls
- Section view is default (stored in localStorage, defaults to `true`)
- When enabled, pages are grouped by their `section` field
- Pages without a section are grouped under "No Section"
- "No Section" appears at the top of the list
- Sections displayed as folders (📁 icon) with folder names
- Pages displayed as documents (📄 icon)
- Pages within each section sorted alphabetically by title
- Section preference persisted in localStorage (`arcadium_nav_section_view`)

**Files**:
- `client/src/components/navigation/NavigationTree.jsx` - Main implementation
- `client/src/styles.css` - Section grouping styles

### Table of Contents Enhancements

#### Sticky Positioning with Auto-Scroll

**Feature**: Table of Contents follows viewport as user scrolls, with automatic scrolling to keep active section visible

**Implementation**:
- **Sticky Container**: TOC container uses CSS `position: sticky` with `top: 1.5rem` to stay within viewport
- **Height Constraint**: Container has `max-height: calc(100vh - 3rem)` to prevent exceeding viewport
- **Scrollable List**: TOC list (`arc-toc-list`) has `overflow-y: auto` when content exceeds container height
- **Auto-Scroll Logic**: `useEffect` hook monitors `activeSection` changes and scrolls TOC list to keep active item visible
  - Calculates if active item is above or below visible area
  - Scrolls with 20px padding from top/bottom edges
  - Uses smooth scroll behavior for better UX
  - Only scrolls when TOC is taller than viewport (no unnecessary scrolling)
- **Custom Scrollbar**: Thin, styled scrollbar for better visual appearance

**Behavior**:
- TOC container stays fixed relative to viewport as page content scrolls
- When TOC list is taller than viewport, it becomes scrollable
- Active section automatically scrolls into view when it changes
- Smooth transitions prevent jarring movements

**Files**:
- `client/src/components/navigation/TableOfContents.jsx` - Main implementation with auto-scroll logic
- `client/src/styles.css` - Sticky positioning and scrollbar styling

### Editor Enhancements

#### Link Dialog Improvements

**Feature**: Enhanced link insertion dialog with improved page search

**Implementation**:
- **Client-side filtering**: All pages fetched once, filtered client-side
- **Alphabetical sorting**: Pages sorted by title on fetch
- **Title-based search**: Filters by page title (case-insensitive, space/special-character forgiving)
- **Dropdown height limit**: Limited to 4 items with scrollbar
- **Slug resolution**: Automatically resolves slugs to page IDs for internal links
- **Dropdown visibility**: Shows on focus, hides on blur (with delay for click handling)

**Files**:
- `client/src/components/editor/LinkDialog.jsx` - Main implementation
- `client/src/components/editor/LinkDialog.css` - Dropdown height and styling

#### Save Navigation

**Feature**: After successful page save, navigate back to view mode

**Implementation**:
- `updateMutation.onSuccess` navigates to `/pages/${pageId}` (view mode)
- `createMutation.onSuccess` navigates to `/pages/${data.id}` (view mode)
- User sees saved page in view mode instead of staying in editor

**Files**:
- `client/src/pages/EditPage.jsx` - Navigation logic in mutation callbacks

### User Experience Enhancements

#### Theme Toggle

**Feature**: Light/dark mode toggle with system preference detection

**Implementation**:
- ThemeToggle component in header
- Respects system preferences (prefers-color-scheme)
- Persists user choice in localStorage
- All components adapt to theme via CSS variables

**Files**:
- `client/src/components/common/ThemeToggle.jsx`
- `client/src/components/common/ThemeToggle.css`

#### Share Button

**Feature**: Share page functionality with copy link

**Implementation**:
- ShareButton component in PageView header
- Copy page link to clipboard
- Fallback to Web Share API if available
- Success/error notifications

**Files**:
- `client/src/components/common/ShareButton.jsx`
- `client/src/components/common/ShareButton.css`
- `client/src/utils/share.js` - Share utilities

#### Service Status Indicator

**Feature**: Visual indicator of overall service health in header

**Implementation**:
- ServiceStatusIndicator component in header
- Shows overall status (healthy/degraded/unhealthy/unknown)
- Color-coded indicator light
- Click to navigate to service management page
- Auto-refreshes every 15 seconds

**Files**:
- `client/src/components/common/ServiceStatusIndicator.jsx`
- `client/src/components/common/ServiceStatusIndicator.css`
- `client/src/services/api/services.js` - Service status API

#### Notification System

**Feature**: User feedback notifications (success, error, info)

**Implementation**:
- NotificationProvider context
- NotificationContainer component
- Toast-style notifications
- Auto-dismiss after timeout
- Manual dismiss option

**Files**:
- `client/src/components/common/NotificationProvider.jsx`
- `client/src/components/common/NotificationContainer.jsx`
- `client/src/components/common/Notification.jsx`

#### Profile Page

**Feature**: User profile page showing account information and permissions

**Implementation**:
- ProfilePage component
- Displays username, email, user ID
- Shows role and permissions
- Redirects to sign-in if not authenticated

**Files**:
- `client/src/pages/ProfilePage.jsx`

#### Service Management Page

**Feature**: Admin page for monitoring and managing all Arcadium services

**Implementation**:
- ServiceManagementPage component
- Displays status of all services
- Manual refresh button
- Service control actions (start/stop/restart)
- Status notes editing
- Export service status report

**Files**:
- `client/src/pages/ServiceManagementPage.jsx`
- `client/src/services/api/services.js` - Service management API

---

## Technical Stack

### Framework
- **React 18+** with React Router v6
- **Vite** as build tool

### Editor
- **Tiptap** (`@tiptap/react`) - WYSIWYG editor
- Extensions: starter-kit, link, image, table, code-block, markdown

### State Management
- **React Query / TanStack Query** - Server state
- **Context API** - Client state (auth, theme, notifications)

### Styling
- **Global CSS** with CSS variables for theming
- Modern, book-like reading experience

### HTTP Client
- **Axios** with interceptors for auth and error handling

### Code Highlighting
- **Prism.js** - Syntax highlighting for code blocks

---

## Component Structure

```
src/
  components/
    layout/
      Header.jsx          # Header with search, auth, theme toggle, service status
      Footer.jsx
      Layout.jsx
      Sidebar.jsx          # Left sidebar with NavigationTree
    navigation/
      NavigationTree.jsx   # Hierarchical navigation with section view toggle
      Breadcrumb.jsx
      PageNavigation.jsx   # Previous/Next navigation
      TableOfContents.jsx  # Right sidebar TOC
      Backlinks.jsx        # Right sidebar backlinks
    content/
      (integrated into PageView)
    comments/
      CommentsList.jsx
      CommentItem.jsx
      CommentForm.jsx
    editor/
      Editor.jsx           # Tiptap editor
      EditorToolbar.jsx   # Formatting toolbar
      MetadataForm.jsx    # Page metadata editor
      LinkDialog.jsx      # Link insertion dialog with page search
      ImageUploadDialog.jsx
      TableDialog.jsx
    page/
      DeleteArchiveDialog.jsx  # Confirmation dialog
    common/
      ThemeToggle.jsx     # Light/dark mode toggle
      ShareButton.jsx     # Share page functionality
      ServiceStatusIndicator.jsx  # Service health indicator
      NotificationProvider.jsx    # Notification context
      NotificationContainer.jsx   # Notification display
      Notification.jsx           # Individual notification
  pages/
    HomePage.jsx
    PageView.jsx          # Main reading view
    EditPage.jsx          # WYSIWYG editor
    SearchPage.jsx        # Search results
    IndexPage.jsx         # Alphabetical index
    PageHistoryPage.jsx   # Version history list
    PageVersionView.jsx   # View specific version
    PageVersionCompare.jsx # Compare versions
    ProfilePage.jsx       # User profile
    ServiceManagementPage.jsx  # Service status management
    SignInPage.jsx        # Authentication
  services/
    api/
      client.js           # Axios instance
      pages.js            # Page API calls
      comments.js         # Comment API calls
      search.js           # Search API calls
      navigation.js       # Navigation API calls
      auth.js            # Auth integration
      services.js        # Service status API
  utils/
    markdown.js          # Markdown conversion
    linkHandler.js      # Link processing
    syntaxHighlight.js  # Code highlighting
    share.js            # Share utilities
    slug.js             # Slug generation
```

---

## Testing Strategy

### Unit Tests
- Component tests (React Testing Library)
- Utility function tests
- API service tests (mocked)
- **Status**: ✅ Comprehensive coverage (523+ client tests)
  - All components fully tested
  - Edge cases covered
  - Error scenarios handled

### Integration Tests
- User flows (create page, edit page, comment)
- Navigation flows
- Search flows
- Metadata editing flows
- **Status**: ✅ Core flows tested (11+ integration tests)

### E2E Tests
- **Playwright** - Full browser testing
- Critical user journeys:
  - Page viewing with syntax highlighting
  - Navigation (breadcrumbs, tree, prev/next)
  - Table of Contents scrolling and highlighting
  - Backlinks navigation
  - Link processing (internal vs external)
- **Status**: ✅ E2E test suite implemented (32+ tests)
- **Run**: `npm run test:e2e` from `client/` directory

---

## Future Enhancements

### Phase 12: Responsive Design (Not Started)
- Mobile (< 768px) layout
- Tablet (768px - 1024px) layout
- Desktop (> 1024px) layout
- Responsive components

### Phase 13: Accessibility (Not Started)
- Keyboard navigation
- Screen reader support
- Visual accessibility (WCAG 2.1 AA compliance)

### Phase 14: Performance Optimization (Not Started)
- Code splitting
- Caching strategies
- Virtualization for long lists
- Image optimization

---

## API Integration

### Authentication
- JWT tokens stored in localStorage
- Token in `Authorization: Bearer <token>` header
- Handle 401 errors (redirect to login)

### Error Handling
- Centralized error handling via Axios interceptors
- User-friendly error messages
- Retry logic for network errors
- Offline detection

### API Service Structure
```
src/services/api/
  client.js          # Axios instance with interceptors
  pages.js           # Page API calls
  comments.js        # Comment API calls
  search.js          # Search API calls
  navigation.js      # Navigation API calls
  auth.js            # Auth integration
  services.js        # Service status API
```

---

## Key Implementation Notes

### Section View Toggle
- **Default**: Section view enabled (stored in localStorage)
- **Grouping**: Pages grouped by `section` field from database
- **No Section**: Pages without section grouped under "No Section" (appears at top)
- **Icons**: Folders (📁) for sections, documents (📄) for pages
- **Sorting**: Sections sorted alphabetically, "No Section" at top; pages within sections sorted alphabetically

### Link Dialog
- **Client-side filtering**: All pages fetched once, filtered in browser
- **Search**: Case-insensitive, space/special-character forgiving title matching
- **Dropdown**: Limited to 4 items with scrollbar
- **Slug resolution**: Automatically converts slugs to page IDs for internal links

### Save Navigation
- **Behavior**: After successful save, automatically navigates to view mode
- **User Experience**: User sees saved page immediately, not stuck in editor

### Theme System
- **System Preference**: Respects `prefers-color-scheme` media query
- **Persistence**: User choice stored in localStorage
- **CSS Variables**: All components use CSS variables for theme colors

### Notification System
- **Provider**: NotificationProvider context wraps app
- **Types**: Success, error, info, warning
- **Auto-dismiss**: Configurable timeout
- **Manual dismiss**: Click to close

---

## Related Documentation

- [Wiki Service Specification](wiki-service-specification.md) - Complete feature specification
- [Wiki User Interface Design](wiki-user-interface.md) - UI/UX design specifications
- [Wiki Implementation Guide](wiki-implementation-guide.md) - Backend implementation guide
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
