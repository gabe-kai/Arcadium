# Wiki Service Implementation Guide

This guide provides reference documentation for the Wiki Service implementation, including setup instructions, architecture overview, and testing strategies.

## 🎉 Implementation Status: **COMPLETE** ✅

**All phases (1-8) have been successfully implemented!**

- **Total Tests**: 756 tests across all phases, all passing (100%)
- **Phases Complete**: 8/8 (100%)
- **Database Migrations**: Flask-Migrate setup complete ✅
- **Production Ready**: Yes ✅
- **Service Integrations**: Auth Service ✅, Notification Service ✅
- **Performance Optimizations**: Caching ✅, Query Optimization ✅

---

## Table of Contents

1. [Prerequisites & Setup](#prerequisites--setup)
2. [Architecture Overview](#architecture-overview)
3. [Core Features](#core-features)
4. [Service Integrations](#service-integrations)
5. [Testing Strategy](#testing-strategy)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## Prerequisites & Setup

### Requirements

- Python 3.11+ (for Python services)
- PostgreSQL 14+ (for databases)
- Docker and Docker Compose (for local development)
- Node.js 18+ (for client development)

### Initial Setup

**Python Environment:**
This project uses a **shared virtual environment** for all Python services (monorepo approach):

```bash
# From project root, create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Database Setup:**
Each service uses its own PostgreSQL database. See [Database Configuration](../architecture/database-configuration.md) for details.

```sql
-- Create wiki database
CREATE DATABASE arcadium_wiki;
```

**Environment Variables:**
Each service requires a `.env` file. Copy from `.env.example`:

```bash
cd services/wiki
cp .env.example .env
# Edit .env with your database credentials
```

**Database Migrations:**
After setting up the database and environment variables, run migrations to create the schema:

```bash
cd services/wiki
flask db upgrade
```

This will apply all pending migrations and create all tables, indexes, and constraints. See `services/wiki/migrations/README.md` for detailed migration documentation.

**Note:** Never commit `.env` files with real passwords. They are automatically excluded by `.gitignore`.

---

## Architecture Overview

### Core Components

The Wiki Service is built with Flask and follows a service-oriented architecture:

- **Models**: Database models (`Page`, `Comment`, `PageLink`, `PageVersion`, `IndexEntry`, `Image`, `WikiConfig`, `OversizedPageNotification`)
- **Services**: Business logic layer (`PageService`, `CommentService`, `LinkService`, `SearchIndexService`, `VersionService`, `OrphanageService`, `FileService`, `MarkdownService`, `CacheService`, `SizeMonitoringService`, `ServiceStatusService`)
- **Routes**: API endpoints (`page_routes`, `comment_routes`, `search_routes`, `navigation_routes`, `version_routes`, `orphanage_routes`, `admin_routes`, `upload_routes`, `extraction_routes`)
- **Utilities**: Helper functions (`SlugGenerator`, `SizeCalculator`, `SyncUtility`)

### Database Schema

**Separate PostgreSQL Schema**: `wiki` schema for all wiki tables

**Key Tables:**
- `pages` - Page content and metadata
- `comments` - Threaded comments (5 levels deep)
- `page_links` - Bidirectional link tracking
- `page_versions` - Version history with diff data
- `index_entries` - Full-text search index
- `images` - Image uploads
- `wiki_config` - System configuration
- `oversized_page_notifications` - Size limit notifications

**Indexes:**
- Standard indexes on frequently queried fields (parent_id, section, slug, status)
- Partial indexes for filtered queries (is_orphaned, is_system_page, is_keyword, is_manual)
- Composite indexes for version queries (page_id, version DESC)

### File System Integration

- **Storage**: Markdown files in `services/wiki/data/pages/` directory
- **Format**: Markdown with YAML frontmatter for metadata
- **Sync**: Automatic sync via file watcher or manual sync commands
- **Structure**: File system mirrors page hierarchy (folders for sections, files for pages)

---

## Core Features

### Page Management

**CRUD Operations:**
- Create, read, update, delete pages
- Draft/published status management
- Archive/unarchive functionality
- Permission-based access control

**Page Organization:**
- Hierarchical parent-child relationships
- Section-based categorization (independent of hierarchy)
- Order index for custom sorting
- Orphanage system for orphaned pages

**File Integration:**
- Automatic file system sync
- Markdown file storage
- Frontmatter preservation
- AI content management compatible

### Comments System

- Threaded comments (up to 5 levels deep)
- User attribution and timestamps
- Edit/delete own comments
- Recommendation badges for player suggestions
- Collapsible reply threads

### Search & Indexing

- Full-text search with relevance ranking
- Keyword extraction and indexing
- Manual keyword management
- Master index (alphabetical listing)
- Section filtering

### Navigation

- Hierarchical navigation tree
- Breadcrumb navigation
- Previous/Next page navigation
- Section grouping view (toggle between hierarchy and section groups)
- Auto-expand to current page

### Version History

- Automatic versioning on every edit
- Version comparison (side-by-side and inline diff)
- Version restoration
- Diff statistics (added/removed lines, character diff)
- Change summaries

### Orphanage System

- Automatic detection of orphaned pages
- Special "Orphanage" container page
- Bulk reassignment tools
- Individual page reassignment
- Orphan tracking (original parent stored)

### Section Extraction

- Extract selected text to new page
- Extract heading-based sections
- Promote sections from TOC to child/sibling pages
- Automatic link replacement in original page

### File Uploads

- Image upload with validation
- File size limits (configurable)
- Type validation
- Page-image associations

### Admin Dashboard

- Size monitoring and distribution charts
- Configuration management (upload size, page size limits)
- Service status monitoring
- Oversized page notifications
- System statistics

---

## Service Integrations

### Auth Service Integration

**Purpose**: Authentication and authorization

**Integration Points:**
1. **JWT Token Validation** - All authenticated endpoints validate tokens
2. **User Role Checking** - Permission enforcement (viewer, player, writer, admin)
3. **User Profile Lookup** - Display user information in comments and metadata
4. **Admin User for AI Content** - Wiki sync utility uses config-based admin user ID

**Shared Code:**
- `shared/auth/tokens/` - Token validation utilities
- `shared/auth/permissions/` - Permission checking helpers

### Notification Service Integration

**Purpose**: Internal messaging for system notifications

**Integration Points:**
1. **Oversized Page Notifications** - Notify page authors when size limits are exceeded
2. **Service Authentication** - Uses service tokens (not user JWT)
3. **Error Handling** - Non-blocking (failures logged but don't block operations)

**Notification Format:**
```json
{
  "recipient_ids": ["author-uuid"],
  "subject": "Page Size Limit Exceeded",
  "content": "Your page '[Title]' exceeds...",
  "type": "warning",
  "action_url": "/wiki/pages/{slug}",
  "metadata": {
    "page_id": "uuid",
    "notification_type": "oversized_page"
  }
}
```

---

## Testing Strategy

### Test Infrastructure

**Framework**: Pytest with PostgreSQL for accurate testing

**Test Organization:**
```
tests/
├── conftest.py          # Shared fixtures (app, client, db)
├── test_api/           # API endpoint tests
├── test_models/        # Database model tests
├── test_services/      # Service layer tests
├── test_sync/          # Sync utility tests
├── test_integration/   # Integration tests
├── test_performance/   # Performance tests
└── test_utils/         # Utility function tests
```

**Test Page Organization:**
- All pages created during test execution are automatically assigned to the "Regression-Testing" section
- Test fixtures and test code explicitly set `section="Regression-Testing"` when creating pages
- System pages (orphanage, service-status) created during tests also receive this section assignment
- This keeps test data organized and separate from production content

### Running Tests

```bash
# Activate virtual environment first (from project root)
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Run all tests
cd services/wiki
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test suite
pytest tests/test_models/
pytest tests/test_services/
pytest tests/test_api/
pytest tests/test_sync/
```

**Note:**
- **Recommended**: Use PostgreSQL for testing to match production behavior (especially important for UUID handling)
- **Alternative**: SQLite in-memory can be used for faster unit tests, but may have limitations with UUID types
- Set `TEST_DATABASE_URL` environment variable to use PostgreSQL: `postgresql://user:password@host:port/database`
- See "Common Issues & Solutions" section below for detailed setup instructions

### Test Coverage

- **560+ tests** across all phases, all passing (100%)
- Comprehensive coverage including unit, integration, and performance tests
- PostgreSQL-based testing for production accuracy

---

## Common Issues & Solutions

### PostgreSQL Testing Setup

**Important:** While SQLite in-memory databases are faster for unit tests, using PostgreSQL for testing ensures your tests match production behavior. This is especially critical for:
- UUID handling (PostgreSQL has native UUID support)
- Foreign key constraints
- Transaction isolation
- Database-specific features

**Setup:**
```python
# tests/conftest.py
import os

# Use TEST_DATABASE_URL from .env if available, otherwise construct from environment variables
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    # Fall back to constructing from individual variables
    TEST_DB_USER = os.environ.get("arcadium_user")
    TEST_DB_PASSWORD = os.environ.get("arcadium_pass")
    TEST_DB_HOST = os.environ.get("DB_HOST", "localhost")
    TEST_DB_PORT = os.environ.get("DB_PORT", "5432")
    TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "arcadium_testing_wiki")

    if TEST_DB_USER and TEST_DB_PASSWORD:
        TEST_DATABASE_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
        os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
```

**Configuration:**
```python
# config.py
class TestingConfig(Config):
    TESTING = True
    # Test database - uses PostgreSQL for accurate testing (matches production)
    _test_db_url = os.environ.get("TEST_DATABASE_URL")
    if not _test_db_url:
        db_user = os.environ.get("arcadium_user")
        db_pass = os.environ.get("arcadium_pass")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        if db_user and db_pass:
            _test_db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/arcadium_testing_wiki"
    SQLALCHEMY_DATABASE_URI = _test_db_url or "sqlite:///:memory:"

    # Override engine options for testing - disable statement timeout to avoid DDL timeouts
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_pre_ping": True,
        "connect_args": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=0",
        },
    }
```

### Database Fixture Setup

**Problem:** Tests need a clean database state, but dropping/recreating tables can cause timeout issues with PostgreSQL locks.

**Solution:** Use a lightweight approach that creates tables if missing and rolls back transactions:

```python
@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        from app import db

        # Ensure tables exist - don't drop, just create if missing
        # This avoids DROP TABLE timeout issues entirely
        db.create_all()

        yield app

        # Clean up: rollback any uncommitted transactions
        # Don't drop or truncate tables - let them persist between tests
        try:
            db.session.rollback()
            db.session.close()
        except Exception:
            pass
        finally:
            db.session.remove()
```

**Note:** This approach avoids `db.drop_all()` which can cause timeout issues with PostgreSQL. Tests use transaction rollback for isolation instead of dropping tables.

### Test Page Organization

**Test pages created during CI/CD workflows** are automatically assigned to the "Regression-Testing" section for organization. This ensures:
- Test pages are clearly separated from production content
- Easy identification and cleanup of test data
- Consistent organization across test runs

All test fixtures and test code explicitly assign `section="Regression-Testing"` when creating pages. System pages (like `orphanage` and `service-status`) created during tests also receive this section assignment.

### SQLAlchemy Object Detachment

**Problem:** SQLAlchemy objects become detached from the session when used across test fixtures, causing `DetachedInstanceError`.

**Solutions:**

1. **Refresh object before use:**
```python
def test_something(app, test_page):
    with app.app_context():
        db.session.refresh(test_page)  # Reattach to session
        print(test_page.title)  # Works!
```

2. **Use merge to reattach:**
```python
def test_something(app, test_page):
    with app.app_context():
        test_page = db.session.merge(test_page)  # Reattach
        print(test_page.title)  # Works!
```

3. **Return ID instead of object (Best Practice):**
```python
@pytest.fixture
def test_page_id(app, test_user_id):
    """Create a test page and return ID"""
    with app.app_context():
        page = Page(title="Test", slug="test", created_by=test_user_id, ...)
        db.session.add(page)
        db.session.commit()
        return page.id  # Return ID, fetch fresh object in tests

def test_something(app, test_page_id):
    with app.app_context():
        page = Page.query.get(test_page_id)  # Fresh object
        print(page.title)  # Works!
```

**Best Practice:** Use option 3 (return IDs) for fixtures that create database objects, as it ensures fresh objects in each test and avoids detachment issues.

### Authentication Mocking in Tests

**Problem:** API tests need to mock authentication without calling the real Auth Service.

**Solution:** Use decorators and fixtures to mock auth:

```python
# tests/test_api/conftest.py
from unittest.mock import patch

def mock_auth(user_id, role='writer'):
    """Context manager to mock authentication"""
    return patch('app.middleware.auth.get_user_from_token', return_value={
        'id': user_id,
        'role': role,
        'username': 'testuser'
    })

def auth_headers(user_id, role='writer'):
    """Generate auth headers for test requests"""
    return {'Authorization': f'Bearer mock_token_{user_id}_{role}'}

# Usage in tests:
def test_create_page(client, app, test_user_id):
    with mock_auth(test_user_id, 'writer'):
        headers = auth_headers(test_user_id, 'writer')
        resp = client.post('/api/pages', json={...}, headers=headers)
        assert resp.status_code == 201
```

### Debugging Hanging Tests

**Common Causes:**
1. Database connections not closed
2. Threads not terminated
3. File handles not closed
4. Infinite loops in test code

**Debugging Steps:**
```bash
# Run with timeout
timeout 10 pytest tests/test_api/test_page_routes.py::test_health_check -v

# Check for stuck processes
ps aux | grep pytest

# Run with verbose output
pytest -v -s --tb=short tests/
```

---

## Performance Optimizations

### Caching

- **HTML Caching**: Rendered HTML cached with configurable TTL
- **TOC Caching**: Table of contents cached per page
- **Cache Invalidation**: Automatic invalidation on content updates

### Query Optimization

- **Reduced N+1 Queries**: Optimized comment queries
- **Eager Loading**: Strategic use of joinedload for relationships
- **Index Usage**: Proper indexes on frequently queried fields

### Connection Pooling

- **Pool Size**: 10 connections per service (default, configurable)
- **Max Overflow**: 20 connections (configurable)
- **Connection Timeout**: 5 seconds (configurable)
- **Max Idle Time**: 30 minutes (configurable)
- **Pool Pre-ping**: Enabled (verifies connections before use)

---

## API Endpoints

### Page Endpoints

- `GET /api/pages` - List all pages (excludes archived pages)
- `GET /api/pages/{id}` - Get single page (includes `can_delete` and `can_archive` flags)
- `POST /api/pages` - Create page
- `PUT /api/pages/{id}` - Update page
- `DELETE /api/pages/{id}` - Delete page
- `POST /api/pages/{id}/archive` - Archive page
- `DELETE /api/pages/{id}/archive` - Unarchive page

### Comment Endpoints

- `GET /api/pages/{id}/comments` - Get comments
- `POST /api/pages/{id}/comments` - Create comment
- `PUT /api/comments/{id}` - Update comment
- `DELETE /api/comments/{id}` - Delete comment

### Search Endpoints

- `GET /api/search?q={query}` - Full-text search
- `GET /api/index` - Master index (alphabetical listing)

### Navigation Endpoints

- `GET /api/navigation` - Navigation tree (includes section field)
- `GET /api/pages/{id}/breadcrumb` - Breadcrumb path
- `GET /api/pages/{id}/navigation` - Previous/next pages

### Version History Endpoints

- `GET /api/pages/{id}/versions` - Version list
- `GET /api/pages/{id}/versions/{version}` - Get specific version
- `GET /api/pages/{id}/versions/compare?from={v1}&to={v2}` - Compare versions
- `POST /api/pages/{id}/versions/{version}/restore` - Restore version

### Orphanage Endpoints

- `GET /api/orphanage` - Get orphaned pages
- `POST /api/orphanage/reassign` - Reassign pages
- `POST /api/orphanage/clear` - Clear orphanage

### Section Extraction Endpoints

- `POST /api/pages/{id}/extract-selection` - Extract selection
- `POST /api/pages/{id}/extract-heading` - Extract heading
- `POST /api/pages/{id}/promote-section` - Promote from TOC

### Admin Endpoints

- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/dashboard/size-distribution` - Size distribution charts
- `GET /api/admin/oversized-pages` - Oversized pages list
- `POST /api/admin/config/upload-size` - Configure upload size
- `POST /api/admin/config/page-size` - Configure page size
- `GET /api/admin/service-status` - Get service status
- `PUT /api/admin/service-status` - Update service status notes
- `POST /api/admin/service-status/refresh` - Refresh status page

### File Upload Endpoints

- `POST /api/upload/image` - Upload image

---

## Test Page Organization

**All test pages created during CI/CD workflows** are automatically assigned to the "Regression-Testing" section. This organization:
- Keeps test data separate from production content
- Makes test pages easy to identify and manage
- Ensures consistent organization across test runs

**Migration Script**: A one-time migration script (`scripts/migrate_pages_to_regression_testing.py`) was used to move existing test pages to the "Regression-Testing" section. This script is preserved for reference but is no longer needed as all new test pages are automatically assigned to this section.

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
- Automatically cleans up orphaned pages when files are deleted
- Debouncing prevents rapid-fire syncs (waits 1 second after last change)
- Recursively monitors all subdirectories in `data/pages/`
- Only watches `.md` files
- Graceful shutdown on Ctrl+C

For more details, see [Wiki AI Content Management](wiki-ai-content-management.md).

---

## Markdown Processing

### Code Blocks

- **Language specifiers**: Code blocks can include language identifiers (e.g., ` ```python `)
- **Whitespace preservation**: Indentation and newlines are preserved
- **HTML conversion**: Code blocks converted to `<pre><code class="language-{lang}">` HTML
- **Syntax highlighting**: Frontend uses Prism.js for syntax highlighting
- **Multi-line support**: Code blocks can span multiple lines with proper formatting
- **HTML entity escaping**: Code content is properly escaped to prevent HTML injection

### Tables

- **GFM table syntax**: Supports GitHub Flavored Markdown table syntax
- **Pattern**: `| Header | Header |\n|--------|\n| Cell | Cell |`
- **Structure preservation**: Header row structure preserved (`<thead>` / `<tbody>`)
- **HTML escaping**: Table cell content is properly escaped
- **Paragraph wrapping protection**: Tables are protected from paragraph wrapping

### Frontmatter

- **Preservation**: All frontmatter fields (including custom fields from AI systems) are stored in `page.content`
- **Hidden from editor**: Frontend editor only displays markdown content (frontmatter is parsed and stripped)
- **Metadata form**: Standard fields (title, slug, section, status, order) managed through UI
- **Custom fields preserved**: Custom frontmatter fields preserved when users edit pages
- **AI compatible**: AI content management systems can write files with custom frontmatter fields

---

## Future Enhancements

1. **Enhanced Search**: PostgreSQL full-text search (ts_vector) for better search quality
2. **Advanced Keywords**: TF-IDF-based keyword extraction
3. **Real-time Features**: WebSocket support for live notifications
4. **Rate Limiting**: API rate limiting and throttling
5. **API Gateway**: Centralized API gateway for all services
6. **Advanced Caching**: Redis integration for distributed caching
7. **Monitoring**: Enhanced monitoring and alerting
8. **Load Testing**: Comprehensive load and stress testing

---

## Related Documentation

- [Wiki Service Specification](wiki-service-specification.md) - Complete feature specification
- [Wiki User Interface Design](wiki-user-interface.md) - UI/UX design specifications
- [Wiki UI Implementation Guide](wiki-ui-implementation-guide.md) - Frontend implementation guide
- [Wiki AI Content Management](wiki-ai-content-management.md) - AI content workflow
- [Wiki Architecture](architecture/wiki-architecture.md) - System architecture details
- [Wiki API Documentation](api/wiki-api.md) - Complete API reference
