#!/usr/bin/env python3
"""
Setup script for Auth Service database.

Creates the database and schema if they don't exist.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_database_and_schema(db_url, db_name='auth'):
    """
    Create database and schema if they don't exist.
    
    Args:
        db_url: Base database URL (with or without database name)
        db_name: Name of the database to create
    """
    # Parse database URL
    if not db_url.startswith('postgresql://'):
        print(f"Error: Invalid database URL format. Must start with 'postgresql://'")
        return False
    
    # Remove query parameters if present
    db_url_clean = db_url.split('?')[0]
    
    # Extract base URL (everything before the last /)
    if '/' in db_url_clean:
        # Split on / to get parts
        parts = db_url_clean.split('/')
        if len(parts) >= 4:
            # Format: postgresql://user:pass@host:port/dbname
            # We want: postgresql://user:pass@host:port
            base_url = '/'.join(parts[:-1])
        else:
            base_url = db_url_clean
    else:
        base_url = db_url_clean
    
    # Connect to postgres database to create the auth database
    postgres_url = f"{base_url}/postgres"
    
    # Mask password in URL for display
    display_url = postgres_url
    if '@' in postgres_url:
        parts = postgres_url.split('@')
        auth_part = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
        if ':' in auth_part:
            user, _ = auth_part.split(':', 1)
            display_url = postgres_url.replace(auth_part, f"{user}:***")
    print(f"Connecting to PostgreSQL at {display_url}...")
    
    try:
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": db_name})
            
            if result.fetchone():
                print(f"Database '{db_name}' already exists.")
            else:
                print(f"Creating database '{db_name}'...")
                conn.execute(text(f'CREATE DATABASE {db_name}'))
                print(f"Database '{db_name}' created successfully.")
        
        # Now connect to the new database to create schema
        auth_db_url = f"{base_url}/{db_name}"
        print(f"Connecting to database '{db_name}'...")
        auth_engine = create_engine(auth_db_url)
        
        with auth_engine.connect() as conn:
            # Check if schema exists
            result = conn.execute(text(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth'"
            ))
            
            if result.fetchone():
                print("Schema 'auth' already exists.")
            else:
                print("Creating schema 'auth'...")
                conn.execute(text('CREATE SCHEMA auth'))
                conn.commit()
                print("Schema 'auth' created successfully.")
        
        print("\nDatabase setup complete!")
        return True
        
    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("\nPlease ensure PostgreSQL is running and credentials are correct.")
        return False
    except ProgrammingError as e:
        print(f"Error creating database/schema: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Auth Service database')
    parser.add_argument('--db-url', type=str, help='Base database URL (without database name)')
    parser.add_argument('--db-name', type=str, default='arcadium_auth', help='Database name (default: arcadium_auth)')
    
    args = parser.parse_args()
    
    # Get database URL from environment or argument
    if args.db_url:
        db_url = args.db_url
    else:
        # Try to get from environment (load .env file first)
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            # Try to construct from arcadium_user and arcadium_pass
            db_user = os.environ.get('arcadium_user')
            db_pass = os.environ.get('arcadium_pass')
            db_host = os.environ.get('DB_HOST', 'localhost')
            db_port = os.environ.get('DB_PORT', '5432')
            
            if db_user and db_pass:
                db_url = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}'
            else:
                print("Error: DATABASE_URL or (arcadium_user and arcadium_pass) must be set")
                print("Set DATABASE_URL or set arcadium_user and arcadium_pass environment variables")
                sys.exit(1)
    
    success = create_database_and_schema(db_url, args.db_name)
    
    if not success:
        print("\nManual setup instructions:")
        print(f"  1. Connect to PostgreSQL: psql -U postgres")
        print(f"  2. Create database: CREATE DATABASE {args.db_name};")
        print(f"  3. Connect to database: \\c {args.db_name}")
        print(f"  4. Create schema: CREATE SCHEMA auth;")
        sys.exit(1)

if __name__ == '__main__':
    main()
