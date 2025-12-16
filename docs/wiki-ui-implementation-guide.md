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

### ⏳ Frontend UI (Not Started)
- Client directory exists but is empty (placeholder only)
- No UI components implemented
- No routing or state management
- No editor integration

## Implementation Phases

### Phase 1: Foundation & Setup
**Goal**: Set up the frontend framework and basic infrastructure

#### Tasks:
- [ ] Choose frontend framework (React recommended for Tiptap integration)
- [ ] Set up project structure (components, pages, services, utils)
- [ ] Configure build tools (Vite already configured)
- [ ] Set up routing (React Router or similar)
- [ ] Set up state management (Context API, Redux, or Zustand)
- [ ] Configure API service layer (axios or fetch wrapper)
- [ ] Set up authentication integration (JWT token handling)
- [ ] Create base layout components (Header, Footer, Layout)
- [ ] Set up CSS/styling approach (CSS Modules, Tailwind, or styled-components)
- [ ] Configure environment variables for API endpoints

#### Deliverables:
- Working development environment
- Basic routing structure
- API service layer with error handling
- Authentication flow integration
- Base layout with header/footer

---

### Phase 2: Reading View - Core Components
**Goal**: Implement the main reading experience

#### Tasks:
- [ ] **Page Content Component**
  - Render markdown HTML content
  - Apply typography styles (max-width 800px, line-height 1.6-1.8)
  - Syntax highlighting for code blocks (Prism.js or highlight.js)
  - Responsive image handling
  - Table styling
  - Block quote styling
  - Internal vs external link styling

- [ ] **Breadcrumb Navigation**
  - Build breadcrumb trail from page hierarchy
  - Click to navigate to parent pages
  - Display: `Home > Section > Parent > Current Page`

- [ ] **Previous/Next Navigation**
  - Calculate previous/next pages based on order_index
  - Display buttons at bottom of content
  - Handle edge cases (first/last pages)

- [ ] **Page Header**
  - Display page title
  - Show metadata (last updated, word count, size)
  - Edit button (for writers/admins)
  - Status indicator (published/draft)

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Get page content
- `GET /api/pages` - List pages for navigation
- `GET /api/navigation/pages/{page_id}/hierarchy` - Get breadcrumbs

#### Deliverables:
- Fully styled page reading view
- Working navigation (breadcrumbs, prev/next)
- Responsive layout

---

### Phase 3: Navigation Tree (Left Sidebar)
**Goal**: Implement hierarchical page navigation

#### Tasks:
- [ ] **Navigation Tree Component**
  - Fetch and build page hierarchy
  - Expandable/collapsible tree nodes
  - Highlight current page
  - Click to navigate
  - Icons for pages vs sections
  - Hover effects
  - Active state highlighting

- [ ] **Tree Search**
  - Search/filter within tree
  - Highlight matching pages
  - Collapse non-matching branches

- [ ] **Tree Features**
  - Show page count per section
  - Remember expanded state (localStorage)
  - Lazy load children (if needed for performance)

#### API Endpoints Used:
- `GET /api/pages` - Get all pages for tree
- `GET /api/navigation/tree` - Get hierarchical structure

#### Deliverables:
- Functional navigation tree
- Search within tree
- Smooth expand/collapse animations

---

### Phase 4: Table of Contents & Backlinks (Right Sidebar)
**Goal**: Implement right sidebar with TOC and backlinks

#### Tasks:
- [ ] **Table of Contents Component**
  - Auto-generate from page headings (H2-H6)
  - Click to scroll to section (smooth scroll)
  - Highlight current section while scrolling
  - Sticky positioning (stays visible)
  - Indentation for nested headings
  - Active section highlighting
  - Collapsible if page is short

- [ ] **Backlinks Component**
  - Display pages that link to current page
  - Show context snippet (where link appears)
  - Click to navigate to linking page
  - Display backlink count
  - Styled list with hover effects

#### API Endpoints Used:
- `GET /api/pages/{page_id}` - Includes `table_of_contents` and `backlinks`

#### Deliverables:
- Sticky TOC with scroll highlighting
- Functional backlinks section
- Smooth scroll-to-section behavior

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

### Integration Tests
- User flows (create page, edit page, comment)
- Navigation flows
- Search flows

### E2E Tests (Optional)
- Playwright or Cypress
- Critical user journeys

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

1. **Review and approve this implementation guide**
2. **Set up development environment** (Phase 1)
3. **Start with MVP phases** (Phases 1-4, 7-10)
4. **Iterate based on feedback**
5. **Add enhanced features** (Phases 5-6, 11-12)
6. **Polish and optimize** (Phases 13-14)

---

## Notes

- Backend API is complete and ready to consume
- All API endpoints are documented in `docs/api/wiki-api.md`
- Design specifications are in `docs/wiki-user-interface.md`
- This guide assumes React, but can be adapted for other frameworks
- Tiptap is the specified editor (design doc requirement)
- Focus on MVP first, then enhance with additional features
