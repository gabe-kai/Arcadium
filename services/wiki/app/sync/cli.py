"""CLI commands for sync utility"""

import argparse
import signal
import sys

from app import create_app
from app.sync.file_watcher import FileWatcher
from app.sync.sync_utility import SyncUtility


def sync_all_command(force: bool = False, admin_user_id: str = None):
    """Sync all markdown files"""
    app = create_app()

    with app.app_context():
        import uuid

        admin_id = None
        if admin_user_id:
            try:
                admin_id = uuid.UUID(admin_user_id)
            except ValueError:
                print(f"Invalid admin_user_id: {admin_user_id}")
                sys.exit(1)

        sync = SyncUtility(admin_user_id=admin_id)
        stats = sync.sync_all(force=force)

        print("Sync complete:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Created: {stats['created']}")
        print(f"  Updated: {stats['updated']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Deleted (orphaned): {stats.get('deleted', 0)}")
        print(f"  Errors: {stats['errors']}")


def sync_file_command(file_path: str, force: bool = False, admin_user_id: str = None):
    """Sync a specific file"""
    app = create_app()

    with app.app_context():
        import uuid

        admin_id = None
        if admin_user_id:
            try:
                admin_id = uuid.UUID(admin_user_id)
            except ValueError:
                print(f"Invalid admin_user_id: {admin_user_id}")
                sys.exit(1)

        sync = SyncUtility(admin_user_id=admin_id)

        try:
            page, status = sync.sync_file(file_path, force=force)
            if status is True:
                action = "Created"
            elif status is False:
                action = "Updated"
            else:
                action = "Skipped (file not newer)"
            print(f"{action} page: {page.title} (slug: {page.slug})")
        except Exception as e:
            print(f"Error syncing file: {e}")
            sys.exit(1)


def sync_dir_command(directory: str, force: bool = False, admin_user_id: str = None):
    """Sync all files in a directory"""
    app = create_app()

    with app.app_context():
        import uuid

        admin_id = None
        if admin_user_id:
            try:
                admin_id = uuid.UUID(admin_user_id)
            except ValueError:
                print(f"Invalid admin_user_id: {admin_user_id}")
                sys.exit(1)

        sync = SyncUtility(admin_user_id=admin_id)

        try:
            stats = sync.sync_directory(directory, force=force)
            print(f"Sync complete for directory '{directory}':")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Created: {stats['created']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Errors: {stats['errors']}")
        except Exception as e:
            print(f"Error syncing directory: {e}")
            sys.exit(1)


def watch_command(admin_user_id: str = None, debounce: float = 1.0):
    """Watch for file changes and auto-sync"""
    app = create_app()

    # Create watcher
    watcher = FileWatcher(
        app=app, admin_user_id=admin_user_id, debounce_seconds=debounce
    )

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n[WATCHER] Shutting down...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start watching
        watcher.start()

        # Keep running
        while watcher.is_alive():
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"[WATCHER] Error: {e}")
        watcher.stop()
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Wiki sync utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # sync-all command
    parser_all = subparsers.add_parser("sync-all", help="Sync all markdown files")
    parser_all.add_argument(
        "--force", action="store_true", help="Force sync even if file is not newer"
    )
    parser_all.add_argument(
        "--admin-user-id", help="Admin user UUID to assign pages to"
    )

    # sync-file command
    parser_file = subparsers.add_parser("sync-file", help="Sync a specific file")
    parser_file.add_argument(
        "file_path", help="Relative file path (e.g., section/page.md)"
    )
    parser_file.add_argument(
        "--force", action="store_true", help="Force sync even if file is not newer"
    )
    parser_file.add_argument(
        "--admin-user-id", help="Admin user UUID to assign pages to"
    )

    # sync-dir command
    parser_dir = subparsers.add_parser("sync-dir", help="Sync all files in a directory")
    parser_dir.add_argument(
        "directory", help="Directory path (relative to pages directory)"
    )
    parser_dir.add_argument(
        "--force", action="store_true", help="Force sync even if file is not newer"
    )
    parser_dir.add_argument(
        "--admin-user-id", help="Admin user UUID to assign pages to"
    )

    # watch command
    parser_watch = subparsers.add_parser(
        "watch", help="Watch for file changes and auto-sync"
    )
    parser_watch.add_argument(
        "--admin-user-id", help="Admin user UUID to assign pages to"
    )
    parser_watch.add_argument(
        "--debounce",
        type=float,
        default=1.0,
        help="Debounce time in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sync-all":
        sync_all_command(force=args.force, admin_user_id=args.admin_user_id)
    elif args.command == "sync-file":
        sync_file_command(
            args.file_path, force=args.force, admin_user_id=args.admin_user_id
        )
    elif args.command == "sync-dir":
        sync_dir_command(
            args.directory, force=args.force, admin_user_id=args.admin_user_id
        )
    elif args.command == "watch":
        watch_command(admin_user_id=args.admin_user_id, debounce=args.debounce)


if __name__ == "__main__":
    main()
