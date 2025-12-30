"""Tests for health check utility"""

import os
import time
from unittest.mock import MagicMock, patch

from app.utils.health_check import get_health_status


def test_get_health_status_basic():
    """Test basic health status without process info"""
    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=False,
    )

    assert result["status"] == "healthy"
    assert result["service"] == "test-service"
    assert result["version"] == "1.0.0"
    assert "process_info" not in result


@patch("app.utils.health_check.PSUTIL_AVAILABLE", True)
@patch("app.utils.health_check.psutil")
@patch("app.utils.health_check.time.time")
@patch("app.utils.health_check.platform.system")
def test_get_health_status_with_psutil(mock_platform, mock_time, mock_psutil):
    """Test health status with psutil available"""
    # Mock platform to be non-Windows so open_files is called
    mock_platform.return_value = "Linux"

    # Mock time to return consistent values
    current_time = 1000000.0
    mock_time.return_value = current_time

    # Mock process
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.create_time.return_value = current_time - 3600  # 1 hour ago
    mock_process.memory_info.return_value = MagicMock(rss=200 * 1024 * 1024)  # 200 MB
    mock_process.cpu_percent.return_value = 2.5
    mock_process.memory_percent.return_value = 1.5
    mock_process.num_threads.return_value = 8
    mock_process.open_files.return_value = [MagicMock(), MagicMock()]  # 2 files

    # Mock context manager for oneshot()
    mock_oneshot = MagicMock()
    mock_oneshot.__enter__ = MagicMock(return_value=mock_process)
    mock_oneshot.__exit__ = MagicMock(return_value=False)
    mock_process.oneshot.return_value = mock_oneshot

    mock_psutil.Process.return_value = mock_process

    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=True,
    )

    assert result["status"] == "healthy"
    assert result["service"] == "test-service"
    assert result["version"] == "1.0.0"
    assert "process_info" in result
    assert result["process_info"]["pid"] == 12345
    assert result["process_info"]["uptime_seconds"] == 3600.0
    assert result["process_info"]["cpu_percent"] == 2.5
    assert result["process_info"]["memory_mb"] == 200.0
    assert result["process_info"]["memory_percent"] == 1.5
    assert result["process_info"]["threads"] == 8
    assert result["process_info"]["open_files"] == 2


@patch("app.utils.health_check.PSUTIL_AVAILABLE", True)
@patch("app.utils.health_check.psutil")
@patch("app.utils.health_check.platform.system")
def test_get_health_status_windows_skips_open_files(mock_platform, mock_psutil):
    """Test that open_files is skipped on Windows"""
    mock_platform.return_value = "Windows"

    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.create_time.return_value = time.time() - 3600
    mock_process.memory_info.return_value = MagicMock(rss=200 * 1024 * 1024)
    mock_process.cpu_percent.return_value = 2.5
    mock_process.memory_percent.return_value = 1.5
    mock_process.num_threads.return_value = 8

    mock_psutil.Process.return_value = mock_process
    mock_psutil.Process.return_value.oneshot.return_value.__enter__ = MagicMock()
    mock_psutil.Process.return_value.oneshot.return_value.__exit__ = MagicMock(
        return_value=False
    )

    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=True,
    )

    assert result["process_info"]["open_files"] == 0
    # Verify open_files() was never called
    mock_process.open_files.assert_not_called()


@patch("app.utils.health_check.PSUTIL_AVAILABLE", False)
def test_get_health_status_without_psutil():
    """Test health status when psutil is not available"""
    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=True,
    )

    assert result["status"] == "healthy"
    assert result["service"] == "test-service"
    assert result["version"] == "1.0.0"
    assert "process_info" in result
    assert result["process_info"]["pid"] == os.getpid()
    assert result["process_info"]["uptime_seconds"] == 0.0
    assert result["process_info"]["cpu_percent"] == 0.0
    assert result["process_info"]["memory_mb"] == 0.0
    assert result["process_info"]["memory_percent"] == 0.0
    assert result["process_info"]["threads"] == 0
    assert result["process_info"]["open_files"] == 0
    assert "note" in result["process_info"]
    assert "psutil not available" in result["process_info"]["note"]


@patch("app.utils.health_check.PSUTIL_AVAILABLE", True)
@patch("app.utils.health_check.psutil")
def test_get_health_status_psutil_exception(mock_psutil):
    """Test health status when psutil raises an exception inside the try block"""
    # Mock psutil exception classes
    mock_psutil.NoSuchProcess = Exception
    mock_psutil.AccessDenied = Exception

    # Create a mock process that raises an exception when accessing create_time
    # This simulates an exception inside the try block (not when calling Process())
    mock_process = MagicMock()
    mock_process.pid = 12345
    # Make create_time() raise an exception to trigger the except block
    mock_process.create_time.side_effect = AttributeError("Process access denied")

    # Mock context manager for oneshot()
    mock_oneshot = MagicMock()
    mock_oneshot.__enter__ = MagicMock(return_value=mock_process)
    mock_oneshot.__exit__ = MagicMock(return_value=False)
    mock_process.oneshot.return_value = mock_oneshot

    mock_psutil.Process.return_value = mock_process

    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=True,
    )

    assert result["status"] == "healthy"
    assert "process_info" in result
    # When exception occurs, it falls back to os.getpid()
    assert result["process_info"]["pid"] == os.getpid()
    assert result["process_info"]["uptime_seconds"] == 0.0
    assert result["process_info"]["cpu_percent"] == 0.0
    assert result["process_info"]["memory_mb"] == 0.0
    assert result["process_info"]["memory_percent"] == 0.0
    assert result["process_info"]["threads"] == 0
    assert result["process_info"]["open_files"] == 0


def test_get_health_status_with_additional_info():
    """Test health status with additional service-specific info"""
    additional_info = {
        "database": "connected",
        "cache": "operational",
        "queue_size": 0,
    }

    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        additional_info=additional_info,
        include_process_info=False,
    )

    assert result["status"] == "healthy"
    assert result["database"] == "connected"
    assert result["cache"] == "operational"
    assert result["queue_size"] == 0


def test_get_health_status_standard_format():
    """Test that health status conforms to standard format"""
    result = get_health_status(
        service_name="test-service",
        version="1.0.0",
        include_process_info=True,
    )

    # Required fields
    assert "status" in result
    assert "service" in result
    assert "version" in result
    assert "process_info" in result

    # Process info required fields
    process_info = result["process_info"]
    assert "pid" in process_info
    assert "uptime_seconds" in process_info
    assert "cpu_percent" in process_info
    assert "memory_mb" in process_info
    assert "memory_percent" in process_info
    assert "threads" in process_info
    assert "open_files" in process_info

    # Type checks
    assert isinstance(result["status"], str)
    assert isinstance(result["service"], str)
    assert isinstance(result["version"], str)
    assert isinstance(process_info["pid"], int)
    assert isinstance(process_info["uptime_seconds"], (int, float))
    assert isinstance(process_info["cpu_percent"], (int, float))
    assert isinstance(process_info["memory_mb"], (int, float))
    assert isinstance(process_info["memory_percent"], (int, float))
    assert isinstance(process_info["threads"], int)
    assert isinstance(process_info["open_files"], int)
