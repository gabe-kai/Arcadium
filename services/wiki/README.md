# Wiki Service

Documentation and planning wiki service built with Python/Flask.

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
# From project root:
pip install -r requirements.txt

# Note: If psycopg2-binary installation fails (especially on Python 3.14+), try:
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
$env:TEST_DATABASE_URL = "postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
pytest
```

**Linux/Mac (Bash):**
```bash
export FLASK_ENV=testing
export TEST_DATABASE_URL="postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
pytest
```

**Prerequisites:**
- PostgreSQL running locally with test database `wiki_test`
- All dependencies installed from root `requirements.txt`

**Note:** Tests use PostgreSQL (not SQLite) to avoid UUID compatibility issues and match production behavior.

### CI/CD

Tests run automatically on GitHub Actions for:
- Push to `main` or `feature/**` branches
- Pull requests targeting `main`

See [CI/CD Documentation](../../docs/ci-cd.md) for details.

## API Endpoints

- `GET /` - Wiki homepage
- `GET /api/pages` - List all pages
- `GET /api/pages/<page_id>` - Get a specific page
- `POST /api/pages` - Create a new page

