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

Run tests for a specific service:

```bash
# Wiki service tests
cd services/wiki
pytest
```

## Documentation

- [Architecture](docs/architecture/)
- [API Documentation](docs/api/)
- [Game Design](docs/game-design/)
- [Service Specifications](docs/services/)

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all tests pass
4. Submit a pull request
