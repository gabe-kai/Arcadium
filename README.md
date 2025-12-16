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

# Install dependencies
pip install -r requirements.txt

# Note: If psycopg2-binary installation fails (especially on Python 3.14+), try:
pip install psycopg2-binary --only-binary :all:
```

### Database Setup

Each service uses its own PostgreSQL database. See [Database Configuration](docs/architecture/database-configuration.md) for details.

**Default PostgreSQL credentials:**
- Username: `postgres`
- Password: `Le555ecure` (configurable via environment variables)

**Create databases:**
```sql
CREATE DATABASE wiki;
-- Add other service databases as needed
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
export TEST_DATABASE_URL="postgresql://postgres:Le555ecure@localhost:5432/wiki_test"
cd services/wiki
pytest
```

See [CI/CD Documentation](docs/ci-cd.md) for detailed information about the CI setup and troubleshooting.

## Web Client

The web client is a React-based SPA located in `client/`. See [Client README](client/README.md) for setup and development instructions.

**Current Status:**
- ✅ Phase 1: Foundation & Setup (Complete)
- ✅ Phase 2: Reading View - Core Components (Complete)
- 🚧 Phase 3+: Navigation Tree, TOC, Comments, Search, Editor (In Progress)

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
