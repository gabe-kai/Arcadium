"""Tests for file watcher service"""
import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from watchdog.events import FileCreatedEvent, FileModifiedEvent
from app.sync.file_watcher import FileWatcher, MarkdownFileHandler
from app.sync.sync_utility import SyncUtility


def test_markdown_file_handler_init():
    """Test MarkdownFileHandler initialization"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    assert handler.sync_utility == mock_sync
    assert handler.debounce_seconds == 1.0
    assert handler.app == mock_app
    assert handler.pages_dir == "data/pages"
    assert handler.pending_files == {}
    assert handler.timer is None


def test_markdown_file_handler_get_relative_path():
    """Test getting relative path from pages directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        pages_dir = os.path.join(tmpdir, "pages")
        os.makedirs(pages_dir)
        
        mock_sync = MagicMock(spec=SyncUtility)
        mock_sync.pages_dir = pages_dir
        mock_app = MagicMock()
        
        handler = MarkdownFileHandler(
            sync_utility=mock_sync,
            debounce_seconds=1.0,
            app=mock_app
        )
        
        # Test file in pages directory
        test_file = os.path.join(pages_dir, "section", "page.md")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        rel_path = handler._get_relative_path(test_file)
        assert rel_path == "section/page.md"
        
        # Test file outside pages directory
        outside_file = os.path.join(tmpdir, "other.md")
        rel_path = handler._get_relative_path(outside_file)
        assert rel_path is None


def test_markdown_file_handler_should_handle():
    """Test file type checking"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    assert handler._should_handle("page.md") is True
    assert handler._should_handle("page.MD") is True
    assert handler._should_handle("page.txt") is False
    assert handler._should_handle("page") is False


def test_markdown_file_handler_schedule_sync():
    """Test scheduling sync with debouncing"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=0.1,  # Short debounce for testing
        app=mock_app
    )
    
    # Schedule sync
    handler._schedule_sync("test.md")
    
    # Check that file is in pending list
    assert "test.md" in handler.pending_files
    assert handler.timer is not None
    
    # Schedule another sync (should cancel previous timer)
    old_timer = handler.timer
    handler._schedule_sync("test2.md")
    
    # Both files should be pending
    assert "test.md" in handler.pending_files
    assert "test2.md" in handler.pending_files


def test_markdown_file_handler_sync_file():
    """Test syncing a file"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    
    # Create a mock page
    mock_page = MagicMock()
    mock_page.slug = "test-page"
    
    # Mock sync_file to return created status
    mock_sync.sync_file.return_value = (mock_page, True)
    
    mock_app = MagicMock()
    mock_app.app_context.return_value.__enter__ = MagicMock()
    mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "test.md")
        with open(test_file, 'w') as f:
            f.write("# Test")
        
        # Mock pages_dir to point to tmpdir
        handler.pages_dir = tmpdir
        
        # Sync the file
        handler._sync_file("test.md")
        
        # Verify sync was called
        mock_sync.sync_file.assert_called_once_with("test.md", force=False)


def test_markdown_file_handler_on_created():
    """Test handling file creation event"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    # Mock _get_relative_path and _should_handle
    handler._get_relative_path = MagicMock(return_value="test.md")
    handler._should_handle = MagicMock(return_value=True)
    handler._schedule_sync = MagicMock()
    
    # Create event
    event = FileCreatedEvent("data/pages/test.md")
    handler.on_created(event)
    
    # Verify schedule was called
    handler._schedule_sync.assert_called_once_with("test.md")


def test_markdown_file_handler_on_modified():
    """Test handling file modification event"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    # Mock methods
    handler._get_relative_path = MagicMock(return_value="test.md")
    handler._should_handle = MagicMock(return_value=True)
    handler._schedule_sync = MagicMock()
    
    # Create event
    event = FileModifiedEvent("data/pages/test.md")
    handler.on_modified(event)
    
    # Verify schedule was called
    handler._schedule_sync.assert_called_once_with("test.md")


def test_markdown_file_handler_ignores_directories():
    """Test that directory events are ignored"""
    mock_sync = MagicMock(spec=SyncUtility)
    mock_sync.pages_dir = "data/pages"
    mock_app = MagicMock()
    
    handler = MarkdownFileHandler(
        sync_utility=mock_sync,
        debounce_seconds=1.0,
        app=mock_app
    )
    
    handler._schedule_sync = MagicMock()
    
    # Create directory event
    event = FileCreatedEvent("data/pages/section")
    event.is_directory = True
    handler.on_created(event)
    
    # Verify schedule was NOT called
    handler._schedule_sync.assert_not_called()


def test_file_watcher_init():
    """Test FileWatcher initialization"""
    mock_app = MagicMock()
    
    watcher = FileWatcher(
        app=mock_app,
        admin_user_id=None,
        debounce_seconds=2.0
    )
    
    assert watcher.app == mock_app
    assert watcher.admin_user_id is None
    assert watcher.debounce_seconds == 2.0
    assert watcher.observer is None
    assert watcher.sync_utility is None
    assert watcher.handler is None


def test_file_watcher_start():
    """Test starting the file watcher"""
    mock_app = MagicMock()
    mock_app.app_context.return_value.__enter__ = MagicMock()
    mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
    mock_app.config.get.return_value = "data/pages"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('app.sync.file_watcher.SyncUtility') as mock_sync_class, \
             patch('app.sync.file_watcher.Observer') as mock_observer_class, \
             patch('os.path.abspath', return_value=tmpdir), \
             patch('os.path.exists', return_value=True), \
             patch('os.makedirs'):
            
            mock_sync = MagicMock()
            mock_sync.pages_dir = tmpdir
            mock_sync_class.return_value = mock_sync
            
            mock_observer = MagicMock()
            mock_observer_class.return_value = mock_observer
            
            watcher = FileWatcher(app=mock_app)
            watcher.start()
            
            # Verify observer was created and started
            mock_observer_class.assert_called_once()
            mock_observer.schedule.assert_called_once()
            mock_observer.start.assert_called_once()


def test_file_watcher_stop():
    """Test stopping the file watcher"""
    mock_app = MagicMock()
    watcher = FileWatcher(app=mock_app)
    
    # Create mock observer
    mock_observer = MagicMock()
    watcher.observer = mock_observer
    
    watcher.stop()
    
    # Verify observer was stopped
    mock_observer.stop.assert_called_once()
    mock_observer.join.assert_called_once()


def test_file_watcher_is_alive():
    """Test checking if watcher is alive"""
    mock_app = MagicMock()
    watcher = FileWatcher(app=mock_app)
    
    # No observer yet
    assert watcher.is_alive() is False
    
    # With observer
    mock_observer = MagicMock()
    mock_observer.is_alive.return_value = True
    watcher.observer = mock_observer
    
    assert watcher.is_alive() is True
