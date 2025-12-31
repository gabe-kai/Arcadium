# Wiki Service

Documentation and planning wiki service built with Python/Flask.

## Quick Start

1. Flask Server
```bash
..\services\wiki
flask run
```

2. Automatic Sync (File Watcher)
```bash
..\services\wiki\
python -m app.sync watch
```

3. Auth Service
```bash
..\services\auth
flask run --port 8000
```

4. Client
```bash
..\client

```

## Setup

1. Activate the project virtual environment (from project root):
```bash
# On Windows:
..\venv\Scripts\activate
# On Linux/Mac:
source ../venv/bin/activate
```

2. Install dependencies (if not already installed):
```bash
# From project root (installs shared dependencies)
pip install -r requirements.txt

# From services/wiki (installs wiki-specific dependencies)
cd services/wiki
pip install -r requirements.txt
```

**Note:** The root `requirements.txt` contains shared dependencies (Flask, SQLAlchemy, psycopg2-binary, etc.). The service-specific `requirements.txt` only contains wiki-specific packages (Flask-CORS, PyYAML, watchdog, etc.).

**If psycopg2-binary installation fails (especially on Python 3.14+):**
```bash
pip install psycopg2-binary --only-binary :all:
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
flask db upgrade
```

4. Start the service:
```bash
flask run
```

The service will be available at `http://localhost:5000` by default.

## Content Format

### Markdown with YAML Frontmatter

Pages are stored as Markdown with YAML frontmatter for metadata:

```yaml
---
title: Page Title
slug: page-slug
section: Section Name
status: published
tags: [ai, content, wiki]
author: AI Assistant
---
# Page Content

Markdown content here...
```

**Important Notes:**
- **Frontmatter is preserved in database** - All frontmatter fields (including custom fields from AI systems) are stored in the `page.content` field
- **Frontmatter is hidden from editor** - The frontend editor only displays the markdown content (frontmatter is parsed and stripped for display)
- **Metadata form** - Standard fields (title, slug, section, status, order) are managed through the Metadata Form UI
- **Custom fields preserved** - Custom frontmatter fields (e.g., `tags`, `author`, `category`) are preserved when users edit pages
- **Code blocks** - Code blocks (```language\ncode```) are properly converted to HTML with language classes, whitespace preservation, and syntax highlighting support
- **Tables** - GFM (GitHub Flavored Markdown) tables are properly converted to HTML with full structure preservation:
  - Pattern: `| Header | Header |\n|--------|\n| Cell | Cell |`
  - Supports multiple rows and columns
  - Header row structure preserved (`<thead>` / `<tbody>`)
  - HTML escaping in table cells
  - Tables protected from paragraph wrapping
- **AI system compatible** - AI content management systems can write files with custom frontmatter fields, and they will be preserved through the sync and edit workflow

## Frontend Integration

The Wiki Service API is configured to work with the React frontend client:

- **CORS enabled** - Allows requests from `http://localhost:3000` (React dev server)
- **HTML format support** - API endpoints accept `?format=html` query parameter for styled HTML responses
- **JSON API** - All endpoints return JSON by default for programmatic access

The frontend client is located in `client/` and connects to the API at `http://localhost:5000/api`.

## File Sync Utility

The wiki service includes a sync utility for syncing markdown files to the database. This is especially useful for AI agents writing wiki content.

### Manual Sync Commands

```bash
# Sync all markdown files
python -m app.sync sync-all

# Sync a specific file
python -m app.sync sync-file data/pages/section/page.md

# Sync a directory
python -m app.sync sync-dir data/pages/section/

# Force sync (ignore modification time)
python -m app.sync sync-all --force

# Specify admin user ID
python -m app.sync sync-all --admin-user-id <uuid>
```

### Automatic Sync (File Watcher)

Start the file watcher to automatically sync files when they're created or modified:

```bash
# Start watching (runs until Ctrl+C)
python -m app.sync watch

# With custom debounce time (default: 1.0 seconds)
python -m app.sync watch --debounce 2.0

# With custom admin user ID
python -m app.sync watch --admin-user-id <uuid>
```

**Watcher Features:**
- Automatically syncs files when created or modified
- Debouncing prevents rapid-fire syncs (waits 1 second after last change)
- Recursively monitors all subdirectories in `data/pages/`
- Only watches `.md` files
- Graceful shutdown on Ctrl+C

**When to Use:**
- **Watch mode**: For continuous development, AI agent workflows, or real-time automatic syncing
- **Manual sync**: For batch operations, one-time syncs, or when you want control over when syncing happens

For more details, see [Wiki AI Content Management](../../docs/wiki-ai-content-management.md).

## Markdown Processing

### Code Blocks

The wiki service includes comprehensive support for code blocks in markdown:

- **Language specifiers**: Code blocks can include language identifiers (e.g., ` ```python `)
- **Whitespace preservation**: Indentation and newlines are preserved in code blocks
- **HTML conversion**: Code blocks are converted to `<pre><code class="language-{lang}">` HTML
- **Syntax highlighting**: Frontend uses Prism.js for syntax highlighting
- **Multi-line support**: Code blocks can span multiple lines with proper formatting
- **HTML entity escaping**: Code content is properly escaped to prevent HTML injection

**Example:**
```markdown
```python
def hello():
    print("Hello")
    return True
```
```

**Backend Tests**: 7 comprehensive tests covering all code block scenarios
**Frontend Tests**: 4 tests for code block rendering in PageView

## Testing

### Running Tests Locally

```bash
# From services/wiki directory
pytest
```

### Running Tests with CI Configuration

To verify tests will pass in CI before pushing:

**Windows (PowerShell):**
```powershell
$env:FLASK_ENV = "testing"
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly:
# $env:TEST_DATABASE_URL = "postgresql://$env:arcadium_user:$env:arcadium_pass@localhost:5432/arcadium_testing_wiki"
pytest
```

**Linux/Mac (Bash):**
```bash
export FLASK_ENV=testing
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly:
# export TEST_DATABASE_URL="postgresql://${arcadium_user}:${arcadium_pass}@localhost:5432/wiki_test"
pytest
```

**Prerequisites:**
- PostgreSQL running locally with test database `arcadium_testing_wiki`
- `.env` file configured with database credentials (`DATABASE_URL` or `arcadium_user`/`arcadium_pass`)
- All dependencies installed from root `requirements.txt`

**Note:** Tests use PostgreSQL (not SQLite) to avoid UUID compatibility issues and match production behavior. The test database URL is automatically constructed from your `.env` credentials if `TEST_DATABASE_URL` is not explicitly set.

### CI/CD

Tests run automatically on GitHub Actions for:
- Push to `main` or `feature/**` branches
- Pull requests targeting `main`

See [CI/CD Documentation](../../docs/ci-cd.md) for details.

## Service Management

The Wiki Service includes a Service Management feature that provides real-time monitoring of all Arcadium services.

### Service Status Dashboard

Access the Service Management page at `/services` in the web client. The dashboard displays:

- **Service Health Status**: Real-time status (🟢 healthy, 🟡 degraded, 🔴 unhealthy) for all services
- **Process Information**: PID, uptime, CPU usage, memory usage, threads, open files
- **Service Details**: Version, description, response times, error messages
- **Service Logs**: View recent logs for Wiki Service and Auth Service
- **Copy Functionality**: Copy individual service info or full status report

### Status Indicator

A status indicator in the navigation bar (visible to all users) shows overall system health:
- 🟢 Green: All services healthy
- 🟡 Amber: One or more services degraded
- 🔴 Red: One or more services unhealthy
- ⚪ Gray: Status unknown (loading or error)

Clicking the status indicator opens the Service Management page.

### Auto-Refresh

Service status automatically refreshes every 15 seconds when the page is active.

### Automatic Status Page Updates

The "Arcadium Service Status" wiki page (slug: `service-status`) is automatically updated every 10 minutes by a background scheduler:

- **First update**: Runs immediately when the Wiki Service starts
- **Subsequent updates**: Aligned to 10-minute intervals (00, 10, 20, 30, 40, 50 minutes past each hour)
- The scheduler runs as a daemon thread and logs all operations
- Manual updates can still be triggered via the `/api/admin/service-status/refresh` endpoint

### Monitored Services

The system monitors:
- Wiki Service (self-monitoring with process info)
- Auth Service (with logs)
- File Watcher Service (AI Content Management)
- Notification Service
- Game Server
- Web Client
- Admin Service
- Assets Service
- Chat Service
- Leaderboard Service
- Presence Service

For detailed documentation, see [Service Management Page](../../docs/wiki-service-status-page.md).

## API Endpoints

### Page Endpoints
- `GET /` - Wiki homepage
- `GET /api/pages` - List all pages (excludes archived pages)
- `GET /api/pages/<page_id>` - Get a specific page (includes `can_delete` and `can_archive` flags)
- `POST /api/pages` - Create a new page
- `PUT /api/pages/<page_id>` - Update a page
- `DELETE /api/pages/<page_id>` - Delete a page (requires writer/admin role, writers can only delete own pages)
- `POST /api/pages/<page_id>/archive` - Archive a page (requires writer/admin role, writers can only archive own pages)
- `DELETE /api/pages/<page_id>/archive` - Unarchive a page (requires writer/admin role, writers can only unarchive own pages)

**Note**: Archived pages are hidden from list views, search results, and index views. Only admins and writers (with permission) can view archived pages.

### Admin Endpoints
- `GET /api/admin/service-status` - Get status of all Arcadium services
- `POST /api/admin/service-status/refresh` - Trigger immediate status check of all services
- `GET /api/admin/logs` - Get recent logs from Wiki Service (query params: `limit`, `level`)
- `PUT /api/admin/service-status` - Update manual status notes for a service (admin only)
