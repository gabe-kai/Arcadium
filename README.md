# Arcadium

A large-scale game project with wiki documentation, game server, and web client.

## Project Structure

This is a monorepo containing:
- **Wiki Service** - Documentation and planning wiki (Python/Flask)
- **Game Server** - Core game logic (Go)
- **Web Client** - Browser-based game client
- **Side Services** - Supporting services (auth, presence, chat, etc.)

## Development Setup

### Prerequisites

- Python 3.11+ (for Python services)
- Go 1.21+ (for game server)
- PostgreSQL 14+ (for databases)
- Node.js 18+ (for web client)

### Python Environment

This project uses a single virtual environment for all Python services:

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install shared dependencies (from project root)
pip install -r requirements.txt

# Install service-specific dependencies
# For Auth Service:
pip install -r services/auth/requirements.txt
# For Wiki Service:
pip install -r services/wiki/requirements.txt

# Note: If psycopg2-binary installation fails (especially on Python 3.14+), try:
pip install psycopg2-binary --only-binary :all:
```

**See [Requirements Structure](docs/requirements-structure.md) for details on the hierarchical requirements system.**

### Database Setup

Each service uses its own PostgreSQL database. See [Database Configuration](docs/architecture/database-configuration.md) for details.

**Database Credentials:**
- Username: Set via `arcadium_user` environment variable
- Password: Set via `arcadium_pass` environment variable
- The user has full permissions to do anything in the database
- These variables are used across all Arcadium services for consistency

**Create databases:**
```sql
-- All databases use arcadium_ prefix
CREATE DATABASE arcadium_wiki;
CREATE DATABASE arcadium_auth;
-- Test databases use arcadium_testing_ prefix
CREATE DATABASE arcadium_testing_wiki;
CREATE DATABASE arcadium_testing_auth;
```

### Running Services

#### Wiki Service

```bash
cd services/wiki
# Set up environment variables (copy .env.example to .env)
cp .env.example .env
# Edit .env with your configuration

# Run migrations
flask db upgrade

# Start the service
flask run
```

## Testing

### Local Testing

Run tests for a specific service:

```bash
# Wiki service tests
cd services/wiki
pytest
```

### CI/CD

The project uses GitHub Actions for continuous integration. Tests run automatically on:
- Push to `main` or `feature/**` branches
- Pull requests targeting `main`

**To run tests locally with CI configuration:**
```bash
# Set environment variables (matches CI)
export FLASK_ENV=testing
# TEST_DATABASE_URL will be constructed from arcadium_user and arcadium_pass if not set
# Or set explicitly: export TEST_DATABASE_URL="postgresql://${arcadium_user}:${arcadium_pass}@localhost:5432/arcadium_testing_wiki"
cd services/wiki
pytest
```

See [CI/CD Documentation](docs/ci-cd.md) for detailed information about the CI setup and troubleshooting.

## Web Client

The web client is a React-based SPA located in `client/`. See [Client README](client/README.md) for setup and development instructions.

**Current Status:**
- ✅ Phase 1: Foundation & Setup (Complete)
- ✅ Phase 2: Reading View - Core Components (Complete)
- ✅ Phase 3: Navigation Tree (Complete)
- ✅ Phase 4: Table of Contents & Backlinks (Complete)
- ✅ Phase 7: WYSIWYG Editor Integration (Complete)
- ✅ Phase 8: Page Metadata Editor (Complete)
- ✅ Authentication System (Sign In/Register UI Complete)
- 🚧 Phase 5: Comments System (Planned)
- 🚧 Phase 6: Search Interface (Planned)

## Documentation

- [Architecture](docs/architecture/)
- [API Documentation](docs/api/)
- [Game Design](docs/game-design/)
- [Service Specifications](docs/services/)
- [Wiki UI Implementation Guide](docs/wiki-ui-implementation-guide.md)
- [CI/CD](docs/ci-cd.md)

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all tests pass
4. Submit a pull request
