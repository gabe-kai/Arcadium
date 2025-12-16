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

## API Endpoints

- `GET /` - Wiki homepage
- `GET /api/pages` - List all pages
- `GET /api/pages/<page_id>` - Get a specific page
- `POST /api/pages` - Create a new page

