"""Tests for sync utility CLI commands"""

from unittest.mock import MagicMock, patch

import pytest
from app.sync.cli import main, sync_all_command, sync_dir_command, sync_file_command


def test_sync_all_command_success(capsys):
    """Test sync-all command success"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        # Setup mocks
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_all.return_value = {
            "total_files": 5,
            "created": 3,
            "updated": 2,
            "skipped": 0,
            "errors": 0,
        }
        mock_sync_class.return_value = mock_sync

        sync_all_command(force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Sync complete:" in captured.out
        assert "Total files: 5" in captured.out
        assert "Created: 3" in captured.out
        assert "Updated: 2" in captured.out


def test_sync_all_command_with_force(capsys):
    """Test sync-all command with force flag"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_all.return_value = {
            "total_files": 2,
            "created": 0,
            "updated": 2,
            "skipped": 0,
            "errors": 0,
        }
        mock_sync_class.return_value = mock_sync

        sync_all_command(force=True, admin_user_id=None)

        # Verify force=True was passed
        mock_sync.sync_all.assert_called_once_with(force=True)


def test_sync_all_command_with_admin_user_id(capsys):
    """Test sync-all command with admin user ID"""
    import uuid

    admin_id = uuid.uuid4()

    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_all.return_value = {
            "total_files": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }
        mock_sync_class.return_value = mock_sync

        sync_all_command(force=False, admin_user_id=str(admin_id))

        # Verify admin_user_id was passed
        mock_sync_class.assert_called_once_with(admin_user_id=admin_id)


def test_sync_all_command_invalid_admin_user_id(capsys):
    """Test sync-all command with invalid admin user ID"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class, pytest.raises(SystemExit):
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync_class.return_value = MagicMock()

        sync_all_command(force=False, admin_user_id="not-a-uuid")

        captured = capsys.readouterr()
        assert "Invalid admin_user_id" in captured.out


def test_sync_file_command_success(capsys):
    """Test sync-file command success"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_page = MagicMock()
        mock_page.title = "Test Page"
        mock_page.slug = "test-page"

        mock_sync = MagicMock()
        mock_sync.sync_file.return_value = (mock_page, True)
        mock_sync_class.return_value = mock_sync

        sync_file_command("test.md", force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Created page: Test Page" in captured.out
        assert "slug: test-page" in captured.out


def test_sync_file_command_updated(capsys):
    """Test sync-file command when page is updated"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_page = MagicMock()
        mock_page.title = "Updated Page"
        mock_page.slug = "updated-page"

        mock_sync = MagicMock()
        mock_sync.sync_file.return_value = (mock_page, False)
        mock_sync_class.return_value = mock_sync

        sync_file_command("updated.md", force=True, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Updated page: Updated Page" in captured.out


def test_sync_file_command_skipped(capsys):
    """Test sync-file command when page is skipped"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_page = MagicMock()
        mock_page.title = "Skipped Page"
        mock_page.slug = "skipped-page"

        mock_sync = MagicMock()
        mock_sync.sync_file.return_value = (mock_page, None)
        mock_sync_class.return_value = mock_sync

        sync_file_command("skipped.md", force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Skipped (file not newer)" in captured.out


def test_sync_file_command_error(capsys):
    """Test sync-file command handles errors"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class, pytest.raises(SystemExit):
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_file.side_effect = FileNotFoundError("File not found")
        mock_sync_class.return_value = mock_sync

        sync_file_command("missing.md", force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Error syncing file" in captured.out
        assert "File not found" in captured.out


def test_sync_dir_command_success(capsys):
    """Test sync-dir command success"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_directory.return_value = {
            "total_files": 3,
            "created": 2,
            "updated": 1,
            "skipped": 0,
            "errors": 0,
        }
        mock_sync_class.return_value = mock_sync

        sync_dir_command("section1", force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Sync complete for directory 'section1':" in captured.out
        assert "Total files: 3" in captured.out
        assert "Created: 2" in captured.out
        assert "Updated: 1" in captured.out


def test_sync_dir_command_error(capsys):
    """Test sync-dir command handles errors"""
    with patch("app.sync.cli.create_app") as mock_create_app, patch(
        "app.sync.cli.SyncUtility"
    ) as mock_sync_class, pytest.raises(SystemExit):
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_app.return_value = mock_app

        mock_sync = MagicMock()
        mock_sync.sync_directory.side_effect = ValueError("Directory not found")
        mock_sync_class.return_value = mock_sync

        sync_dir_command("nonexistent", force=False, admin_user_id=None)

        captured = capsys.readouterr()
        assert "Error syncing directory" in captured.out
        assert "Directory not found" in captured.out


def test_main_sync_all(capsys):
    """Test main CLI with sync-all command"""
    with patch("sys.argv", ["sync", "sync-all"]), patch(
        "app.sync.cli.sync_all_command"
    ) as mock_command:
        main()
        mock_command.assert_called_once_with(force=False, admin_user_id=None)


def test_main_sync_all_with_flags(capsys):
    """Test main CLI with sync-all and flags"""
    with patch(
        "sys.argv", ["sync", "sync-all", "--force", "--admin-user-id", "test-uuid"]
    ), patch("app.sync.cli.sync_all_command") as mock_command:
        main()
        mock_command.assert_called_once_with(force=True, admin_user_id="test-uuid")


def test_main_sync_file(capsys):
    """Test main CLI with sync-file command"""
    with patch("sys.argv", ["sync", "sync-file", "test.md"]), patch(
        "app.sync.cli.sync_file_command"
    ) as mock_command:
        main()
        mock_command.assert_called_once_with("test.md", force=False, admin_user_id=None)


def test_main_sync_file_with_force(capsys):
    """Test main CLI with sync-file and force flag"""
    with patch("sys.argv", ["sync", "sync-file", "test.md", "--force"]), patch(
        "app.sync.cli.sync_file_command"
    ) as mock_command:
        main()
        mock_command.assert_called_once_with("test.md", force=True, admin_user_id=None)


def test_main_sync_dir(capsys):
    """Test main CLI with sync-dir command"""
    with patch("sys.argv", ["sync", "sync-dir", "section1"]), patch(
        "app.sync.cli.sync_dir_command"
    ) as mock_command:
        main()
        mock_command.assert_called_once_with(
            "section1", force=False, admin_user_id=None
        )


def test_main_no_command(capsys):
    """Test main CLI with no command shows help"""
    with patch("sys.argv", ["sync"]), patch(
        "argparse.ArgumentParser.print_help"
    ) as mock_help, pytest.raises(SystemExit):
        main()
        mock_help.assert_called_once()
