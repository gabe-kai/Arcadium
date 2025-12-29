#!/usr/bin/env python
"""
Database setup script for Wiki Service.

This script creates the PostgreSQL database if it doesn't exist,
then runs migrations to set up the schema.

Usage:
    python scripts/setup_database.py
"""

import os
import sys

from sqlalchemy import create_engine, text

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


def create_database_if_not_exists(database_url, db_name):
    """Create database if it doesn't exist"""
    # Parse database URL to get connection info without database name
    # Format: postgresql://user:password@host:port/database
    if "postgresql://" not in database_url:
        print(f"Error: Invalid database URL format: {database_url}")
        return False

    # Extract components
    parts = database_url.replace("postgresql://", "").split("@")
    if len(parts) != 2:
        print("Error: Could not parse database URL")
        return False

    auth_part = parts[0]
    host_part = parts[1]

    # Get database name from host_part
    if "/" in host_part:
        host_port, _ = host_part.rsplit("/", 1)
    else:
        host_port = host_part

    # Connect to postgres database to create the target database
    admin_url = f"postgresql://{auth_part}@{host_port}/postgres"

    try:
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            exists = result.fetchone()

            if not exists:
                print(f"Creating database '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")

        engine.dispose()
        return True
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def main():
    """Main setup function"""
    # Load configuration
    app_config = config.get(os.environ.get("FLASK_ENV", "development"))

    database_url = app_config.SQLALCHEMY_DATABASE_URI

    if not database_url or database_url.startswith("sqlite"):
        print("Error: This script requires PostgreSQL. SQLite is not supported.")
        sys.exit(1)

    # Extract database name from URL
    if "/" in database_url:
        db_name = database_url.rsplit("/", 1)[-1].split("?")[0]
    else:
        print("Error: Could not extract database name from URL")
        sys.exit(1)

    print(f"Setting up database: {db_name}")
    # Mask password in URL for display
    if "@" in database_url:
        url_parts = database_url.split("@")
        auth_part = (
            url_parts[0].split("://")[1] if "://" in url_parts[0] else url_parts[0]
        )
        if ":" in auth_part:
            user = auth_part.split(":")[0]
            display_url = database_url.replace(auth_part, f"{user}:***")
        else:
            display_url = database_url
    else:
        display_url = database_url
    print(f"Database URL: {display_url}")

    # Create database if it doesn't exist
    if not create_database_if_not_exists(database_url, db_name):
        print("\nPlease create the database manually:")
        print(f'  psql -U postgres -c "CREATE DATABASE {db_name};"')
        sys.exit(1)

    print("\nDatabase setup complete!")
    print("\nNext steps:")
    print("  1. Run migrations: flask db upgrade")
    print("  2. Start the service: flask run")


if __name__ == "__main__":
    main()
