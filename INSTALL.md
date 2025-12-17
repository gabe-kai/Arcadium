# Installation Guide

## Quick Start

### 1. Create Virtual Environment

```bash
# From project root
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install shared dependencies (from project root)
pip install -r requirements.txt

# If psycopg2-binary fails to build (Python 3.14), use wheels:
pip install psycopg2-binary --only-binary :all:

# Install service-specific dependencies
pip install -r services/auth/requirements.txt
pip install -r services/wiki/requirements.txt
```

### 3. Set Up Environment Variables

```bash
# Set database credentials (used across all services)
export arcadium_user=your-username
export arcadium_pass=your-password

# Or on Windows:
set arcadium_user=your-username
set arcadium_pass=your-password
```

### 4. Set Up Databases

```bash
# Create databases
psql -U postgres
CREATE DATABASE arcadium_wiki;
CREATE DATABASE arcadium_auth;
```

### 5. Run Migrations

```bash
# Auth Service
cd services/auth
set FLASK_APP=app
flask db upgrade

# Wiki Service
cd services/wiki
set FLASK_APP=app
flask db upgrade
```

## Troubleshooting

### psycopg2-binary Build Errors (Python 3.14)

If you get build errors when installing `psycopg2-binary`:

```bash
# Option 1: Use wheels only (recommended)
pip install psycopg2-binary --only-binary :all:

# Option 2: Use psycopg (version 3, better Python 3.14 support)
pip install "psycopg[binary]>=3.1.0"
```

### Requirements Structure

This project uses a hierarchical requirements structure:
- **Root `requirements.txt`**: Shared dependencies (Flask, SQLAlchemy, psycopg2-binary, etc.)
- **Service `requirements.txt`**: Service-specific dependencies only

See [Requirements Structure](docs/requirements-structure.md) for details.
