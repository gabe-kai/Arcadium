# Wiki Service Implementation Guide

This guide provides reference documentation for the Wiki Service, including setup instructions, testing strategies, and best practices.

## 🎉 Implementation Status: **COMPLETE** ✅

**All phases (1-8) have been successfully implemented!**

- **Total Tests**: 561 tests across all phases, all passing (100%)
- **Phases Complete**: 8/8 (100%)
- **Database Migrations**: Flask-Migrate setup complete ✅
- **Production Ready**: Yes ✅
- **Service Integrations**: Auth Service ✅, Notification Service ✅
- **Performance Optimizations**: Caching ✅, Query Optimization ✅

## Prerequisites

- Python 3.11+ (for Python services)
- PostgreSQL 14+ (for databases)
- Docker and Docker Compose (for local development)
- Node.js 18+ (for client development, if needed)

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

## Implementation Summary

The Wiki Service has been fully implemented with the following components:

### Core Features
- **Page Management**: Full CRUD operations with file system integration
- **Comments**: Threaded comments with 5-level depth support
- **Search**: Full-text search and keyword indexing
- **Navigation**: Hierarchy, breadcrumbs, and previous/next navigation
- **Version History**: Complete version tracking with diff support
- **Orphanage System**: Automatic detection and management of orphaned pages
- **Section Extraction**: Extract sections to new pages
- **File Uploads**: Image upload with validation
- **Admin Dashboard**: Size monitoring, configuration management, service status

### Service Integrations
- **Auth Service**: JWT token validation and user profile retrieval
- **Notification Service**: Oversized page notifications and internal messaging

### Performance Optimizations
- **Caching**: HTML and TOC caching with configurable TTL
- **Query Optimization**: Reduced N+1 queries for comments
- **Connection Pooling**: Database connection pooling configured

### Testing
- **561 tests** across all phases, all passing (100%)
- Comprehensive coverage including unit, integration, and performance tests
- PostgreSQL-based testing for production accuracy

---

## Implementation Phases Checklist

Use this checklist when implementing a wiki service from scratch:

### Phase 1: Foundation Setup

#### 1.1 Project Structure
- [ ] Set up Flask application structure
- [ ] Configure database connection (PostgreSQL)
- [ ] Set up environment variables (.env with DATABASE_URL)
- [ ] Create base configuration files (config.py)
- [ ] Set up shared Python virtual environment (monorepo)
- [ ] Configure test infrastructure (pytest, PostgreSQL for tests)

#### 1.2 Database Setup
- [ ] Create database models (all tables):
  - `pages` (with `is_system_page` field)
  - `comments` (with `thread_depth` field)
  - `page_links`
  - `index_entries` (with `is_manual` field)
  - `page_versions`
  - `images` and `page_images`
  - `wiki_config`
  - `oversized_page_notifications`
- [ ] Set up Flask-Migrate
- [ ] Create initial migration
- [ ] Create indexes as specified in architecture doc:
  - Standard indexes (parent, section, slug, status, etc.)
  - Partial indexes (is_orphaned, is_system_page, is_keyword, is_manual)
  - Composite indexes (page_versions: page_id, version DESC)
- [ ] Set up database connection pooling

**Testing:**
- [ ] Write model tests (all models)
- [ ] Test database migrations (upgrade/downgrade)
- [ ] Verify schema matches architecture doc

---

### Phase 2: Core Data Models

- [ ] Implement Page model with all fields
- [ ] Add validation for slug uniqueness
- [ ] Implement parent-child relationships
- [ ] Add `is_system_page` flag handling
- [ ] Implement orphanage detection (is_orphaned, orphaned_from fields)
- [ ] Implement Comment model with thread depth
- [ ] Implement PageLink model for bidirectional tracking
- [ ] Implement PageVersion model with diff data
- [ ] Implement IndexEntry model (full-text and keywords)
- [ ] Implement Image and PageImage models
- [ ] Implement WikiConfig model
- [ ] Implement OversizedPageNotification model

**Testing:**
- [ ] Test all model creation and relationships
- [ ] Test constraints and validations
- [ ] Test cascade deletes
- [ ] Test edge cases

---

### Phase 3: File System Integration & Utilities

- [ ] Implement FileService for file operations
- [ ] Implement file path calculation (section/parent hierarchy)
- [ ] Implement MarkdownService (parse frontmatter, render HTML)
- [ ] Implement TOC generation (H2-H6 headings)
- [ ] Implement SlugGenerator (generate and validate slugs)
- [ ] Implement SizeCalculator (word count, content size KB)

**Testing:**
- [ ] Test file operations (create, read, update, delete, move)
- [ ] Test markdown parsing and rendering
- [ ] Test TOC generation
- [ ] Test slug generation and validation
- [ ] Test size calculations

---

### Phase 4: Core Business Logic

#### 4.1 Page Service
- [ ] Implement page CRUD operations
- [ ] Implement draft/published status handling
- [ ] Implement permission checks (can_edit, can_delete)
- [ ] Integrate with FileService

#### 4.2 Orphanage Service
- [ ] Implement orphan detection
- [ ] Implement get_or_create_orphanage
- [ ] Implement page reassignment
- [ ] Implement bulk operations

#### 4.3 Link Service
- [ ] Implement link extraction from markdown
- [ ] Implement bidirectional link tracking
- [ ] Implement link updates on slug changes
- [ ] Implement broken link detection

#### 4.4 Search Index Service
- [ ] Implement full-text indexing
- [ ] Implement keyword extraction
- [ ] Implement manual keyword management
- [ ] Implement search with relevance ranking

#### 4.5 Version Service
- [ ] Implement version creation on updates
- [ ] Implement version retrieval
- [ ] Implement diff calculation
- [ ] Implement rollback functionality

**Testing:**
- [ ] Test all service methods
- [ ] Test integration between services
- [ ] Test error handling
- [ ] Test edge cases

---

### Phase 5: API Endpoints

#### 5.1 Page Endpoints
- [ ] GET /api/pages (list with filters)
- [ ] GET /api/pages/{id} (get single page)
- [ ] POST /api/pages (create page)
- [ ] PUT /api/pages/{id} (update page)
- [ ] DELETE /api/pages/{id} (delete page)

#### 5.2 Comment Endpoints
- [ ] GET /api/pages/{id}/comments (get comments)
- [ ] POST /api/pages/{id}/comments (create comment)
- [ ] PUT /api/comments/{id} (update comment)
- [ ] DELETE /api/comments/{id} (delete comment)
- [ ] Support threaded replies (5 levels deep)

#### 5.3 Search Endpoints
- [ ] GET /api/search?q={query} (search)
- [ ] GET /api/search/master-index (master index)

#### 5.4 Navigation Endpoints
- [ ] GET /api/navigation (navigation tree)
- [ ] GET /api/pages/{id}/breadcrumb (breadcrumb)
- [ ] GET /api/pages/{id}/previous-next (previous/next)

#### 5.5 Version History Endpoints
- [ ] GET /api/pages/{id}/versions (version list)
- [ ] GET /api/pages/{id}/versions/{version} (get version)
- [ ] GET /api/pages/{id}/versions/compare (compare versions)
- [ ] POST /api/pages/{id}/versions/{version}/restore (restore)

#### 5.6 Orphanage Endpoints
- [ ] GET /api/orphanage (get orphaned pages)
- [ ] POST /api/orphanage/reassign (reassign pages)
- [ ] POST /api/orphanage/clear (clear orphanage)

#### 5.7 Section Extraction Endpoints
- [ ] POST /api/pages/{id}/extract-selection (extract selection)
- [ ] POST /api/pages/{id}/extract-heading (extract heading)
- [ ] POST /api/pages/{id}/promote-section (promote from TOC)

#### 5.8 Authentication Middleware
- [ ] Implement require_auth decorator
- [ ] Implement require_role decorator
- [ ] Implement get_user_from_token

#### 5.9 Admin Endpoints
- [ ] GET /api/admin/dashboard/stats (dashboard stats)
- [ ] GET /api/admin/dashboard/size-distribution (size distribution)
- [ ] GET /api/admin/oversized-pages (oversized pages)
- [ ] POST /api/admin/config/upload-size (configure upload size)
- [ ] POST /api/admin/config/page-size (configure page size)
- [ ] GET /api/admin/service-status (get service status)
- [ ] PUT /api/admin/service-status (update service status)
- [ ] POST /api/admin/service-status/refresh (refresh status page)

#### 5.10 File Upload Endpoints
- [ ] POST /api/upload/image (upload image)
- [ ] Validate file size and type
- [ ] Associate images with pages

**Testing:**
- [ ] Test all endpoints (happy paths)
- [ ] Test authentication/authorization
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Test draft filtering
- [ ] Test permission enforcement

---

### Phase 6: Sync Utility (AI Content)

- [ ] Implement file scanner (find markdown files)
- [ ] Implement frontmatter parser
- [ ] Implement database sync logic (create/update pages)
- [ ] Implement parent slug resolution
- [ ] Integrate with LinkService and SearchIndexService
- [ ] Implement CLI commands:
  - [ ] sync-all (sync all files)
  - [ ] sync-file (sync single file)
  - [ ] sync-dir (sync directory)
- [ ] Implement file watcher service (automatic syncing)
- [ ] Add debouncing to prevent rapid-fire syncs
- [ ] Handle admin user assignment

**Testing:**
- [ ] Test file scanning
- [ ] Test sync logic (create/update)
- [ ] Test error handling
- [ ] Test CLI commands
- [ ] Test file watcher
- [ ] Test integration with other services

---

### Phase 7: Admin Dashboard Features

#### 7.1 Size Monitoring
- [ ] Implement SizeMonitoringService
- [ ] Calculate page sizes and word counts
- [ ] Track oversized pages
- [ ] Generate size distribution charts
- [ ] Auto-create notifications when limit is set
- [ ] Auto-resolve when pages are fixed

#### 7.2 Configuration Management
- [ ] Implement file upload size limits (presets + custom)
- [ ] Implement page size limits with notification creation
- [ ] Store configuration in WikiConfig
- [ ] Validate configuration values

#### 7.3 Service Status Page
- [ ] Implement ServiceStatusService
- [ ] Health check integration for all services
- [ ] Generate system page with status table
- [ ] Support manual status notes
- [ ] Create API endpoints for status management

**Testing:**
- [ ] Test size monitoring
- [ ] Test configuration management
- [ ] Test service status checks
- [ ] Test API endpoints

---

### Phase 8: Integration & Polish

#### 8.1 Auth Service Integration
- [ ] Create AuthServiceClient
- [ ] Implement JWT token verification
- [ ] Implement user profile retrieval
- [ ] Update auth middleware to use Auth Service

#### 8.2 Notification Service Integration
- [ ] Create NotificationServiceClient
- [ ] Integrate oversized page notifications
- [ ] Support service token authentication
- [ ] Handle errors gracefully (non-blocking)

#### 8.3 Performance Optimization
- [ ] Implement CacheService (HTML and TOC caching)
- [ ] Add cache invalidation on content updates
- [ ] Optimize comment queries (reduce N+1)
- [ ] Configure connection pooling

**Testing:**
- [ ] Test Auth Service integration
- [ ] Test Notification Service integration
- [ ] Test caching performance
- [ ] Test query optimization

---

## Testing Strategy

### Unit Tests
- Test each model, service, and utility independently
- Mock external dependencies (Auth Service, Notification Service)
- Aim for >80% code coverage

### Integration Tests
- Test API endpoints with database
- Test file system operations
- Test service-to-service communication

### End-to-End Tests
- Test complete user workflows:
  - Create page → Edit → Delete
  - Comment → Reply (5 levels)
  - Search → Navigate → View
  - Admin: Configure → Monitor → Notify

### Test Data Setup
```python
# tests/fixtures/
- test_pages.json
- test_users.json
- test_comments.json
- test_links.json
```

### Continuous Testing
```bash
# Activate virtual environment first (from project root)
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Run all tests
cd services/wiki
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific phase
pytest tests/test_models/
pytest tests/test_services/
pytest tests/test_api/
pytest tests/test_sync/
```

**Note:**
- **Recommended:** Use PostgreSQL for testing to match production behavior (especially important for UUID handling)
- **Alternative:** SQLite in-memory can be used for faster unit tests, but may have limitations with UUID types
- Set `TEST_DATABASE_URL` environment variable to use PostgreSQL: `postgresql://user:password@host:port/database`
- See "Testing Best Practices and Common Issues" section below for detailed setup instructions

---

## Validation Checklist

After each phase, validate against design documents:

### Specification Validation
- [ ] All user roles implemented correctly
- [ ] All permissions enforced
- [ ] All features from specification present

### API Validation
- [ ] All endpoints match API documentation
- [ ] Request/response formats correct
- [ ] Error handling matches spec
- [ ] Permissions match spec

### Architecture Validation
- [ ] Database schema matches architecture doc
- [ ] File structure matches spec
- [ ] Data flow matches diagrams
- [ ] Component structure matches

### UI Validation
- [ ] TOC generation matches UI spec
- [ ] Comment threading matches spec
- [ ] Navigation matches spec
- [ ] Editor features match spec

---

## Common Pitfalls to Avoid

1. **Don't skip tests** - Write tests as you implement
2. **Don't hardcode permissions** - Use middleware
3. **Don't forget draft filtering** - Check all list endpoints
4. **Don't ignore file system** - Keep files and DB in sync
5. **Don't skip validation** - Validate against design docs regularly

---

## Testing Best Practices and Common Issues

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
from sqlalchemy import create_engine, text

# PostgreSQL test database configuration
TEST_DB_NAME = 'arcadium_testing_wiki'
TEST_DB_USER = 'postgres'
TEST_DB_PASSWORD = 'your_password'
TEST_DB_HOST = 'localhost'
TEST_DB_PORT = '5432'

TEST_DATABASE_URL = f'postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}'

def ensure_test_database():
    """Ensure the test database exists"""
    admin_url = f'postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres'
    try:
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
            )
            exists = result.fetchone()
            if not exists:
                conn.execute(text(f'CREATE DATABASE {TEST_DB_NAME}'))
        engine.dispose()
    except Exception:
        pass  # Database might already exist
```

**Configuration:**
```python
# config.py
class TestingConfig(Config):
    TESTING = True
    # TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
```

### Critical: Database Fixture Teardown

**Problem:** Tests may leave data in the database, causing test pollution and failures.

**Solution:** Always clean up test data in fixtures:

```python
@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()  # Critical: Clean up after tests
```

**Best Practice:** Use transactions and rollback for isolation:

```python
@pytest.fixture
def db_session(app):
    """Create database session with transaction rollback"""
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.session

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### SQLAlchemy Object Detachment in Test Fixtures

**Problem:** SQLAlchemy objects become detached from the session when used across test fixtures, causing `DetachedInstanceError`.

**Example Issue:**
```python
@pytest.fixture
def test_page(app, test_user_id):
    """Create a test page"""
    page = Page(title="Test", slug="test", created_by=test_user_id, ...)
    db.session.add(page)
    db.session.commit()
    return page  # Object is detached after session closes

def test_something(test_page):
    print(test_page.title)  # DetachedInstanceError!
```

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

3. **Keep session open in fixture:**
```python
@pytest.fixture
def test_page(app, test_user_id):
    """Create a test page"""
    with app.app_context():
        page = Page(title="Test", slug="test", created_by=test_user_id, ...)
        db.session.add(page)
        db.session.commit()
        yield page
        # Session stays open until fixture cleanup
```

4. **Return ID instead of object:**
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

**Best Practice:** Use option 4 (return IDs) for fixtures that create database objects, as it ensures fresh objects in each test and avoids detachment issues.

### Avoiding Duplicate Service Calls

**Problem:** Multiple tests calling the same service method can cause conflicts or unexpected behavior.

**Example:**
```python
def test_create_page(app, test_user_id):
    page_service = PageService()
    page = page_service.create_page(...)  # Creates page

def test_update_page(app, test_user_id):
    page_service = PageService()
    page = page_service.create_page(...)  # Creates another page - might conflict!
```

**Solution:** Use fixtures to create shared test data:

```python
@pytest.fixture
def test_page(app, test_user_id):
    """Create a test page fixture"""
    with app.app_context():
        page = Page(title="Test", slug="test", created_by=test_user_id, ...)
        db.session.add(page)
        db.session.commit()
        return page.id

def test_update_page(app, test_page_id, test_user_id):
    """Use fixture instead of creating new page"""
    page_service = PageService()
    page = page_service.update_page(test_page_id, ...)  # Uses fixture
```

### Test Fixture Organization

**Structure:**
```
tests/
├── conftest.py          # Shared fixtures (app, client, db)
├── test_api/
│   └── conftest.py     # API-specific fixtures (auth mocking)
├── test_models/
│   └── conftest.py     # Model-specific fixtures
└── test_services/
    └── conftest.py     # Service-specific fixtures
```

**Best Practices:**
- Put shared fixtures in `conftest.py` at the appropriate level
- Use descriptive fixture names (`test_user_id`, `test_page_id`)
- Return IDs from fixtures that create database objects
- Use `pytest.fixture(scope='function')` for test isolation
- Use `pytest.fixture(scope='module')` sparingly (only for expensive setup)

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

## Next Steps

### Pre-Production Checklist
1. ✅ Code review against design documents - **COMPLETE**
2. ✅ Performance testing - **COMPLETE** (caching, query optimization)
3. ⏳ Security audit - **TODO**
4. ⏳ User acceptance testing - **TODO**
5. ✅ Documentation review - **COMPLETE**
6. ⏳ Deployment preparation - **TODO**

### Future Enhancements
1. **Enhanced Search**: PostgreSQL full-text search (ts_vector) for better search quality
2. **Advanced Keywords**: TF-IDF-based keyword extraction
3. **Real-time Features**: WebSocket support for live notifications
4. **Rate Limiting**: API rate limiting and throttling
5. **API Gateway**: Centralized API gateway for all services
6. **Advanced Caching**: Redis integration for distributed caching
7. **Monitoring**: Enhanced monitoring and alerting
8. **Load Testing**: Comprehensive load and stress testing
