#!/usr/bin/env python3
"""
Drop all Arcadium databases to prepare for fresh migration.

This script drops all databases that match the Arcadium naming pattern:
- arcadium_* (production/development databases)
- arcadium_testing_* (test databases)

WARNING: This will delete all data in these databases!
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def get_database_url():
    """Get base database URL from environment"""
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_user = os.environ.get('arcadium_user')
        db_pass = os.environ.get('arcadium_pass')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        
        if db_user and db_pass:
            db_url = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}'
        else:
            print("Error: DATABASE_URL or (arcadium_user and arcadium_pass) must be set")
            sys.exit(1)
    
    # Remove database name and query parameters
    if '/' in db_url:
        base_url = db_url.rsplit('/', 1)[0]
    else:
        base_url = db_url
    
    if '?' in base_url:
        base_url = base_url.split('?')[0]
    
    return base_url

def get_arcadium_databases(engine):
    """Get list of all Arcadium databases"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT datname FROM pg_database "
            "WHERE datname LIKE 'arcadium_%' "
            "ORDER BY datname"
        ))
        return [row[0] for row in result]

def drop_database(engine, db_name):
    """Drop a database"""
    try:
        # Terminate all connections to the database first
        with engine.connect() as conn:
            conn.execute(text(
                f"SELECT pg_terminate_backend(pid) "
                f"FROM pg_stat_activity "
                f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid()"
            ))
            conn.commit()
        
        # Drop the database
        with engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS {db_name}'))
            conn.commit()
        return True
    except Exception as e:
        print(f"  Error dropping {db_name}: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drop all Arcadium databases')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    print("Arcadium Database Cleanup Script")
    print("=" * 50)
    print()
    print("WARNING: This will delete all data in Arcadium databases!")
    print("Databases to be dropped:")
    print("  - arcadium_* (production/development)")
    print("  - arcadium_testing_* (test databases)")
    print()
    
    if not args.yes:
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    # Get database URL
    base_url = get_database_url()
    postgres_url = f"{base_url}/postgres"
    
    print(f"\nConnecting to PostgreSQL...")
    try:
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        
        # Get list of Arcadium databases
        databases = get_arcadium_databases(engine)
        
        if not databases:
            print("No Arcadium databases found.")
            return
        
        print(f"\nFound {len(databases)} Arcadium database(s):")
        for db in databases:
            print(f"  - {db}")
        
        print("\nDropping databases...")
        dropped = []
        failed = []
        
        for db_name in databases:
            print(f"  Dropping {db_name}...", end=' ')
            if drop_database(engine, db_name):
                print("✓")
                dropped.append(db_name)
            else:
                print("✗")
                failed.append(db_name)
        
        print(f"\nSummary:")
        print(f"  Dropped: {len(dropped)}")
        if failed:
            print(f"  Failed: {len(failed)}")
            for db in failed:
                print(f"    - {db}")
        
        print("\nDatabase cleanup complete!")
        print("\nNext steps:")
        print("  1. Run migrations: flask db upgrade (in each service)")
        print("  2. Verify databases were created correctly")
        
    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("\nPlease ensure:")
        print("  - PostgreSQL is running")
        print("  - arcadium_user and arcadium_pass are set correctly")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
