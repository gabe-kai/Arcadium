# Requirements File Structure

## Overview

The Arcadium project uses a hierarchical requirements structure to avoid duplication and make dependency management easier.

## Structure

### Root `requirements.txt`
Contains **shared dependencies** used by all Python services:
- Flask, Flask-SQLAlchemy, Flask-Migrate
- psycopg2-binary (PostgreSQL adapter)
- python-dotenv
- pytest, pytest-cov
- Other shared utilities

### Service-Specific `requirements.txt`
Each service has its own `requirements.txt` that contains **only service-specific dependencies**:
- `services/auth/requirements.txt` - PyJWT, bcrypt, Flask-Limiter, etc.
- `services/wiki/requirements.txt` - Flask-CORS, PyYAML, watchdog, etc.

## Installation

### Option 1: Install Both (Recommended)
```bash
# From project root
pip install -r requirements.txt -r services/auth/requirements.txt
```

### Option 2: Install Separately
```bash
# Step 1: Install shared dependencies
pip install -r requirements.txt

# Step 2: Install service-specific dependencies
cd services/auth
pip install -r requirements.txt
```

## Benefits

1. **No Duplication**: Shared dependencies defined once
2. **Clear Separation**: Easy to see what's service-specific vs shared
3. **Easier Updates**: Update shared dependencies in one place
4. **Smaller Service Files**: Service requirements only list what's unique

## Adding New Dependencies

### Shared Dependency (used by multiple services)
Add to root `requirements.txt`:
```txt
# Root requirements.txt
new-shared-package==1.0.0
```

### Service-Specific Dependency
Add to service's `requirements.txt`:
```txt
# services/auth/requirements.txt
auth-specific-package==1.0.0
```

## PostgreSQL Adapter Note

The root `requirements.txt` includes `psycopg2-binary>=2.9.11` which supports Python 3.14.

If installation fails:
```bash
pip install psycopg2-binary --only-binary :all:
```

Alternatively, you can use `psycopg` (version 3):
```bash
pip install "psycopg[binary]>=3.1.0"
```

Note: SQLAlchemy supports both psycopg2 and psycopg without code changes.
