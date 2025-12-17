# Arcadium Client (Wiki UI)

Web client application for the **Arcadium Wiki**. This frontend consumes the Wiki Service API and implements the UI described in `docs/wiki-user-interface.md` and `docs/wiki-ui-implementation-guide.md`.

## Features (Current Status)

### ✅ Phase 1: Foundation & Setup (Complete)
- React 18 + Vite-based SPA
- React Router v6+ with future flags enabled for v7 behavior
- Base layout shell:
  - Header with logo and search input
  - Sidebar placeholder (future navigation tree)
  - Main content area
  - Footer
- Axios API client pointing at the Wiki Service with CORS support
- React Query for server state management
- Auth context ready (JWT token storage + Authorization header)
- Testing infrastructure (Vitest + React Testing Library + jsdom)

### ✅ Phase 2: Reading View - Core Components (Complete)
- **PageView** – Full reading experience with:
  - Page content rendering (markdown → HTML)
  - Page title and metadata display (updated_at, word_count, size, status)
  - **Breadcrumb navigation** – Shows path from root to current page
  - **Previous/Next navigation** – Sequential page navigation buttons
  - **Syntax highlighting** – Prism.js for code blocks (JS, TS, Python, Bash, JSON, Markdown, CSS, SQL)
  - **Enhanced content styling**:
    - Styled tables with striped rows and hover effects
    - Responsive images with rounded corners and shadows
    - Enhanced blockquotes with decorative styling
    - Internal vs external link distinction (visual indicators)
- **API Integration**:
  - `usePage` hook for page data
  - `useBreadcrumb` hook for breadcrumb trail
  - `usePageNavigation` hook for previous/next pages

### 🚧 In Progress / Planned
- `HomePage` – welcome view (basic implementation)
- `EditPage` – WYSIWYG editor view (Phase 7)
- `SearchPage` – search results (Phase 6)
- `IndexPage` – alphabetical index (Phase 6)
- Navigation Tree sidebar (Phase 3)
- Table of Contents & Backlinks sidebar (Phase 4)
- Comments system (Phase 5)

## Setup

From the `client/` directory:

1. **Install dependencies**

```bash
npm install
```

2. **Start development server**

```bash
npm run dev
```

Then open `http://localhost:3000/` in your browser.

3. **Build for production**

```bash
npm run build
```

## Configuration

The Wiki UI talks to the Wiki Service API. Configure the base URL via Vite env variables:

- **`VITE_WIKI_API_BASE_URL`** – Wiki API base URL (default: `http://localhost:5000/api`)

Example `.env` in `client/`:

```bash
VITE_WIKI_API_BASE_URL=http://localhost:5000/api
```

## Testing

### Unit & Integration Tests

Tests use **Vitest** with **jsdom** and **React Testing Library**.

From `client/`:

```bash
# Run all tests
npm test

# Run tests with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### E2E Tests

End-to-end tests use **Playwright** to test the full application in a real browser.

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests in UI mode (interactive)
npm run test:e2e:ui

# Run E2E tests with visible browser
npm run test:e2e:headed

# Debug E2E tests
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

**First time setup:**
```bash
npx playwright install
```

See `e2e/README.md` for detailed E2E testing documentation.

### What’s Covered So Far

- **App shell**
  - `App` renders without crashing
  - Header/footer render expected text
  - Home page renders by default
- **Routing**
  - Root path (`/`) renders `HomePage`
  - `/pages/:pageId` renders `PageView`
  - `/search` renders `SearchPage`
- **API client**
  - Axios instance uses correct base URL and timeout
- **PageView component**
  - Loading, error, and success states
  - Metadata display
  - Content rendering
- **Navigation components**
  - `Breadcrumb` – All states (null, empty, single item, multiple items, current page detection)
  - `PageNavigation` – All states (both links, one link, disabled states)
- **Layout components**
  - `Layout`, `Header`, `Footer` basic rendering

### Test Coverage

- **Component tests**: 430+ test cases covering all components
  - PageView, Breadcrumb, PageNavigation, NavigationTree
  - TableOfContents, Backlinks, Layout, Footer, Sidebar
  - Editor, EditorToolbar, MetadataForm
  - EditPage, HomePage, SearchPage, IndexPage, SignInPage
  - All utility functions
- **Integration tests**: 25+ test cases
  - Page creation/editing flows
  - Metadata integration
  - Navigation flows
  - Authentication flows
- **E2E tests**: 32+ Playwright tests
  - Full user journeys
  - Browser-based testing
  - Authentication flow testing
- **Coverage**: Comprehensive with aggressive edge case coverage
  - All components fully tested
  - Edge cases and error scenarios covered
  - API error handling tested
  - **Total**: 485+ tests across 30 test files

## Related Documentation

- `docs/wiki-user-interface.md` – high-level UI design
- `docs/wiki-ui-implementation-guide.md` – phased UI implementation plan
- `docs/wiki-implementation-guide.md` – backend Wiki Service implementation
- `docs/ci-cd.md` – CI/CD setup for both backend and frontend
- `client/PHASE_8_SUMMARY.md` – Phase 8 implementation details
- `client/TEST_COVERAGE_SUMMARY.md` – Comprehensive test coverage summary

