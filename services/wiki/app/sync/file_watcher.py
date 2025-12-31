"""
File watcher service for automatic syncing of markdown files.

This module provides a file system watcher that monitors the wiki pages directory
and automatically syncs markdown files to the database when they are created or modified.
On file deletion, it performs a full sync to reset the database to match the file system state.

Usage:
    # Start the watcher from CLI
    python -m app.sync watch

    # Or use programmatically
    from app import create_app
    from app.sync.file_watcher import FileWatcher

    app = create_app()
    watcher = FileWatcher(app=app)
    watcher.start()

    # ... watcher runs until stopped ...
    watcher.stop()

Features:
    - Monitors data/pages/ directory recursively
    - Automatically syncs .md files on create/modify events
    - Performs full sync after file deletions to reset database state
    - Debouncing prevents rapid-fire syncs
    - Graceful shutdown on Ctrl+C
    - Error resilient (continues watching on sync errors)

See Also:
    - app.sync.sync_utility: Core sync logic
    - app.sync.cli: CLI commands including watch
    - docs/wiki-ai-content-management.md: Complete documentation
"""

import os
import threading
import time
from typing import Dict, Optional

from app.sync.sync_utility import SyncUtility
from flask import Flask
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class MarkdownFileHandler(FileSystemEventHandler):
    """
    Handler for markdown file system events.

    Processes file creation and modification events, schedules files for syncing
    with debouncing to prevent multiple syncs of the same file in rapid succession.

    On file deletion, schedules a full sync of all files to reset the database
    to match the current file system state. This is useful for cleaning up the
    database after tests or manual file deletions.

    Only handles .md files within the pages directory. Ignores directory events
    and files outside the pages directory.

    Example:
        handler = MarkdownFileHandler(
            sync_utility=sync_utility,
            debounce_seconds=1.0,
            app=flask_app
        )
        observer.schedule(handler, pages_directory, recursive=True)
    """

    def __init__(
        self,
        sync_utility: SyncUtility,
        debounce_seconds: float = 1.0,
        app: Flask = None,
    ):
        """
        Initialize file handler.

        Args:
            sync_utility: SyncUtility instance for syncing files
            debounce_seconds: Wait time before syncing (to handle rapid changes)
            app: Flask application instance (for app context)
        """
        super().__init__()
        self.sync_utility = sync_utility
        self.debounce_seconds = debounce_seconds
        self.app = app
        self.pending_files: Dict[str, float] = {}  # file_path -> timestamp
        self.lock = threading.Lock()
        self.pages_dir = sync_utility.pages_dir
        self.timer: Optional[threading.Timer] = None
        self.deletion_timer: Optional[threading.Timer] = None
        self.deletion_pending = False

    def _get_relative_path(self, file_path: str) -> Optional[str]:
        """
        Get relative path from pages directory.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path or None if not in pages directory
        """
        try:
            pages_abs = os.path.abspath(self.pages_dir)
            file_abs = os.path.abspath(file_path)

            if not file_abs.startswith(pages_abs):
                return None

            # Get relative path
            rel_path = os.path.relpath(file_abs, pages_abs)

            # Normalize path separators
            rel_path = rel_path.replace("\\", "/")

            return rel_path
        except Exception:
            return None

    def _should_handle(self, file_path: str) -> bool:
        """
        Check if file should be handled (is a markdown file).

        Args:
            file_path: File path

        Returns:
            True if file is a markdown file
        """
        return file_path.lower().endswith(".md")

    def _schedule_sync(self, file_path: str):
        """
        Schedule a file for syncing (with debouncing).

        Args:
            file_path: Relative file path
        """
        with self.lock:
            current_time = time.time()
            self.pending_files[file_path] = current_time

            # Cancel existing timer if running
            if self.timer:
                self.timer.cancel()

            # Start new debounce timer
            self.timer = threading.Timer(
                self.debounce_seconds, self._sync_pending_files
            )
            self.timer.start()

    def _sync_pending_files(self):
        """Sync all pending files that have passed the debounce period"""
        with self.lock:
            current_time = time.time()
            files_to_sync = []

            for file_path, timestamp in list(self.pending_files.items()):
                if current_time - timestamp >= self.debounce_seconds:
                    files_to_sync.append(file_path)
                    del self.pending_files[file_path]

        # Sync files outside the lock
        for file_path in files_to_sync:
            self._sync_file(file_path)

    def _schedule_full_sync(self):
        """
        Schedule a full sync after file deletion (with debouncing).

        This will sync all files from the pages directory, effectively
        resetting the database to match the file system state.
        """
        with self.lock:
            self.deletion_pending = True

            # Cancel existing deletion timer if running
            if self.deletion_timer:
                self.deletion_timer.cancel()

            # Start new debounce timer for full sync
            self.deletion_timer = threading.Timer(
                self.debounce_seconds
                * 2,  # Use 2x debounce for deletions to allow multiple deletions
                self._perform_full_sync,
            )
            self.deletion_timer.start()

    def _perform_full_sync(self):
        """
        Perform a full sync of all files in the pages directory.

        This is called after file deletions to reset the database
        to match the current file system state.
        """
        with self.lock:
            if not self.deletion_pending:
                return
            self.deletion_pending = False

        # Full sync operations need Flask app context
        if not self.app:
            print("[WATCHER] Error: No Flask app context available for full sync")
            return

        try:
            with self.app.app_context():
                print("[WATCHER] Performing full sync after file deletion(s)...")
                stats = self.sync_utility.sync_all(force=False)
                print(
                    f"[WATCHER] Full sync complete: "
                    f"{stats['created']} created, "
                    f"{stats['updated']} updated, "
                    f"{stats['skipped']} skipped, "
                    f"{stats.get('deleted', 0)} deleted (orphaned), "
                    f"{stats['errors']} errors"
                )
        except Exception as e:
            print(f"[WATCHER] Error during full sync after deletion: {e}")

    def _sync_file(self, file_path: str):
        """
        Sync a single file.

        Args:
            file_path: Relative file path
        """
        # Sync operations need Flask app context
        if not self.app:
            print("[WATCHER] Error: No Flask app context available")
            return

        try:
            with self.app.app_context():
                # Verify file still exists (might have been deleted)
                full_path = os.path.join(self.sync_utility.pages_dir, file_path)
                if not os.path.exists(full_path):
                    return

                # Sync the file
                page, status = self.sync_utility.sync_file(file_path, force=False)

                if status is True:
                    print(f"[WATCHER] Created: {file_path} (slug: {page.slug})")
                elif status is False:
                    print(f"[WATCHER] Updated: {file_path} (slug: {page.slug})")
                else:
                    print(f"[WATCHER] Skipped: {file_path} (not newer than database)")

        except Exception as e:
            print(f"[WATCHER] Error syncing {file_path}: {e}")

    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if event.is_directory:
            return

        rel_path = self._get_relative_path(event.src_path)
        if rel_path and self._should_handle(rel_path):
            print(f"[WATCHER] File created: {rel_path}")
            self._schedule_sync(rel_path)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if event.is_directory:
            return

        rel_path = self._get_relative_path(event.src_path)
        if rel_path and self._should_handle(rel_path):
            print(f"[WATCHER] File modified: {rel_path}")
            self._schedule_sync(rel_path)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if event.is_directory:
            return

        rel_path = self._get_relative_path(event.src_path)
        if rel_path and self._should_handle(rel_path):
            print(f"[WATCHER] File deleted: {rel_path}")
            # Schedule a full sync to reset database to match file system
            # This ensures the database reflects the current state of files
            self._schedule_full_sync()


class FileWatcher:
    """
    File watcher service for automatic syncing of markdown files.

    Monitors the wiki pages directory for file changes and automatically syncs
    new or modified markdown files to the database. Uses watchdog library for
    efficient file system monitoring.

    The watcher runs continuously until stopped. It handles graceful shutdown
    on SIGINT (Ctrl+C) or SIGTERM signals.

    Example:
        from app import create_app
        from app.sync.file_watcher import FileWatcher

        app = create_app()
        watcher = FileWatcher(
            app=app,
            admin_user_id=None,  # Uses default from config
            debounce_seconds=1.0  # Wait 1 second after last change
        )

        try:
            watcher.start()
            # Watcher runs until interrupted
        except KeyboardInterrupt:
            watcher.stop()

    Attributes:
        app: Flask application instance
        admin_user_id: Admin user UUID for assigning pages (optional)
        debounce_seconds: Debounce time in seconds (default: 1.0)
        observer: Watchdog Observer instance (None until started)
        sync_utility: SyncUtility instance (None until started)
        handler: MarkdownFileHandler instance (None until started)
        pages_abs: Absolute path to pages directory (None until started)

    See Also:
        - MarkdownFileHandler: Event handler for file system events
        - SyncUtility: Core sync logic
        - docs/wiki-ai-content-management.md: Complete usage documentation
    """

    def __init__(
        self,
        app: Flask,
        admin_user_id: Optional[str] = None,
        debounce_seconds: float = 1.0,
    ):
        """
        Initialize file watcher.

        Args:
            app: Flask application instance
            admin_user_id: Admin user UUID (optional)
            debounce_seconds: Debounce time in seconds (default: 1.0)
        """
        self.app = app
        self.admin_user_id = admin_user_id
        self.debounce_seconds = debounce_seconds
        self.observer: Optional[Observer] = None
        self.sync_utility: Optional[SyncUtility] = None
        self.handler: Optional[MarkdownFileHandler] = None
        self.pages_abs: Optional[str] = None

    def start(self):
        """Start watching for file changes"""
        with self.app.app_context():
            # Initialize sync utility
            import uuid

            admin_id = None
            if self.admin_user_id:
                try:
                    admin_id = uuid.UUID(self.admin_user_id)
                except ValueError:
                    print(f"Warning: Invalid admin_user_id: {self.admin_user_id}")

            self.sync_utility = SyncUtility(admin_user_id=admin_id)

            # Get pages directory
            pages_dir = self.sync_utility.pages_dir
            self.pages_abs = os.path.abspath(pages_dir)

            # Ensure directory exists
            if not os.path.exists(self.pages_abs):
                os.makedirs(self.pages_abs, exist_ok=True)
                print(f"[WATCHER] Created pages directory: {self.pages_abs}")

            # Create file handler (needs app context for sync operations)
            self.handler = MarkdownFileHandler(
                sync_utility=self.sync_utility,
                debounce_seconds=self.debounce_seconds,
                app=self.app,
            )

            # Create observer
            self.observer = Observer()
            self.observer.schedule(self.handler, self.pages_abs, recursive=True)

            # Start watching
            self.observer.start()
            print(f"[WATCHER] Started watching: {self.pages_abs}")
            print(f"[WATCHER] Debounce time: {self.debounce_seconds}s")
            print("[WATCHER] Press Ctrl+C to stop")

    def stop(self):
        """Stop watching for file changes"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("[WATCHER] Stopped watching")

    def is_alive(self) -> bool:
        """Check if watcher is running"""
        return self.observer is not None and self.observer.is_alive()
