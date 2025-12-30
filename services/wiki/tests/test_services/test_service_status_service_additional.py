"""Additional tests for service status service - new features"""

import os
import time
from unittest.mock import MagicMock, patch

import requests
from app.services.service_status_service import ServiceStatusService


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_slow_response_degraded(mock_get):
    """Test that slow response time (>1500ms) marks service as degraded"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy", "service": "auth"}
    mock_response.headers.get.return_value = "application/json"
    mock_get.return_value = mock_response

    # Mock time to simulate slow response
    with patch("app.services.service_status_service.time.time") as mock_time:
        mock_time.side_effect = [0.0, 1.6]  # 1.6 seconds elapsed
        result = ServiceStatusService.check_service_health("auth", timeout=2.0)

    assert result["status"] == "degraded"
    assert "status_reason" in result
    assert "Slow response time" in result["status_reason"]
    assert "1500ms threshold" in result["status_reason"]


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_very_slow_response_unhealthy(mock_get):
    """Test that very slow response time (>2000ms) marks service as unhealthy"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy", "service": "auth"}
    mock_response.headers.get.return_value = "application/json"
    mock_get.return_value = mock_response

    # Mock time to simulate very slow response
    with patch("app.services.service_status_service.time.time") as mock_time:
        mock_time.side_effect = [0.0, 2.5]  # 2.5 seconds elapsed
        result = ServiceStatusService.check_service_health("auth", timeout=3.0)

    assert result["status"] == "unhealthy"
    assert "status_reason" in result
    assert "Slow response time" in result["status_reason"]
    assert "2000ms threshold" in result["status_reason"]


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_fast_response_healthy(mock_get):
    """Test that fast response time (<1500ms) keeps service as healthy"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy", "service": "wiki"}
    mock_response.headers.get.return_value = "application/json"
    mock_get.return_value = mock_response

    # Mock time to simulate fast response
    with patch("app.services.service_status_service.time.time") as mock_time:
        mock_time.side_effect = [0.0, 0.1]  # 100ms elapsed
        result = ServiceStatusService.check_service_health("wiki", timeout=2.0)

    assert result["status"] == "healthy"
    assert result.get("status_reason") is None


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_timeout_with_reason(mock_get):
    """Test that timeout includes status reason"""
    mock_get.side_effect = requests.exceptions.Timeout()

    result = ServiceStatusService.check_service_health("auth", timeout=1.0)

    assert result["status"] == "unhealthy"
    assert result["error"] == "Request timeout"
    assert "status_reason" in result
    assert "timed out" in result["status_reason"].lower()
    assert "1.0s" in result["status_reason"]


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_connection_error_with_reason(mock_get):
    """Test that connection error includes status reason"""
    mock_get.side_effect = requests.exceptions.ConnectionError()

    result = ServiceStatusService.check_service_health("game-server")

    assert result["status"] == "unhealthy"
    assert result["error"] == "Connection refused"
    assert "status_reason" in result
    assert "connection refused" in result["status_reason"].lower()


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_404_with_reason(mock_get):
    """Test that 404 error includes status reason"""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = ServiceStatusService.check_service_health("unknown-service")

    assert result["status"] == "unhealthy"
    assert "404" in result["error"]
    assert "status_reason" in result
    assert "404" in result["status_reason"]
    assert "not found" in result["status_reason"].lower()


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_500_with_reason(mock_get):
    """Test that 500 error includes status reason"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    result = ServiceStatusService.check_service_health("auth")

    assert result["status"] == "unhealthy"
    assert "500" in result["error"]
    assert "status_reason" in result
    assert "500" in result["status_reason"]
    assert "experiencing issues" in result["status_reason"].lower()


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_service_reported_degraded(mock_get):
    """Test that service-reported degraded status includes reason"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "degraded",
        "service": "notification",
        "reason": "High latency detected",
    }
    mock_response.headers.get.return_value = "application/json"
    mock_get.return_value = mock_response

    with patch("app.services.service_status_service.time.time") as mock_time:
        mock_time.side_effect = [0.0, 0.1]  # Fast response
        result = ServiceStatusService.check_service_health("notification", timeout=2.0)

    assert result["status"] == "degraded"
    assert "status_reason" in result
    # Should use the service's reported reason
    assert result["status_reason"] == "High latency detected"


@patch("app.services.service_status_service.ServiceStatusService._session.get")
def test_check_service_health_non_json_response_degraded(mock_get):
    """Test that non-JSON response (not HTML) is marked as degraded with reason"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Not JSON")
    mock_response.headers.get.return_value = "text/plain"
    mock_get.return_value = mock_response

    with patch("app.services.service_status_service.time.time") as mock_time:
        mock_time.side_effect = [0.0, 0.1]
        result = ServiceStatusService.check_service_health("unknown", timeout=2.0)

    assert result["status"] == "degraded"
    assert "status_reason" in result
    assert "non-JSON response" in result["status_reason"].lower()


@patch("app.services.service_status_service.psutil")
def test_get_current_process_info_with_psutil(mock_psutil):
    """Test getting current process info when psutil is available"""
    # Mock process
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.create_time.return_value = time.time() - 3600  # 1 hour ago
    mock_process.memory_info.return_value = MagicMock(rss=150 * 1024 * 1024)  # 150 MB
    mock_process.cpu_percent.return_value = 2.5
    mock_process.memory_percent.return_value = 1.2
    mock_process.num_threads.return_value = 8
    mock_process.open_files.return_value = [MagicMock(), MagicMock()]  # 2 files

    mock_psutil.Process.return_value = mock_process
    mock_psutil.Process.return_value.oneshot.return_value.__enter__ = MagicMock()
    mock_psutil.Process.return_value.oneshot.return_value.__exit__ = MagicMock(
        return_value=False
    )

    with patch("app.services.service_status_service.PSUTIL_AVAILABLE", True):
        result = ServiceStatusService.get_current_process_info()

    assert result["pid"] == 12345
    assert result["uptime_seconds"] > 0
    assert result["cpu_percent"] == 2.5
    assert result["memory_mb"] == 150.0
    assert result["memory_percent"] == 1.2
    assert result["threads"] == 8
    assert result["open_files"] == 2


@patch("app.services.service_status_service.psutil")
def test_get_current_process_info_without_psutil():
    """Test getting current process info when psutil is not available"""
    with patch("app.services.service_status_service.PSUTIL_AVAILABLE", False):
        result = ServiceStatusService.get_current_process_info()

    assert result["pid"] == os.getpid()
    assert result["uptime_seconds"] == 0.0
    assert result["cpu_percent"] == 0.0
    assert result["memory_mb"] == 0.0
    assert result["memory_percent"] == 0.0
    assert result["threads"] == 0
    assert result["open_files"] == 0
    assert "note" in result
    assert "psutil not available" in result["note"]


@patch("app.services.service_status_service.psutil")
def test_get_file_watcher_info_found(mock_psutil):
    """Test detecting file watcher process"""
    # Mock process iterator
    mock_process = MagicMock()
    mock_process.info = {
        "pid": 11111,
        "name": "python",
        "cmdline": ["python", "-m", "app.sync", "watch"],
        "create_time": time.time() - 1800,  # 30 minutes ago
        "memory_info": MagicMock(rss=45 * 1024 * 1024),  # 45 MB
        "cpu_percent": 0.1,
        "num_threads": 3,
    }
    mock_process.cpu_percent.return_value = 0.1
    mock_process.memory_percent.return_value = 0.3

    # Mock current process (should be skipped)
    current_process = MagicMock()
    current_process.info = {"pid": os.getpid()}

    mock_psutil.process_iter.return_value = [current_process, mock_process]

    with patch("app.services.service_status_service.PSUTIL_AVAILABLE", True):
        result = ServiceStatusService.get_file_watcher_info()

    assert result is not None
    assert result["is_running"] is True
    assert result["process_info"]["pid"] == 11111
    assert "metadata" in result
    assert "command" in result["metadata"]


@patch("app.services.service_status_service.psutil")
def test_get_file_watcher_info_not_found(mock_psutil):
    """Test when file watcher process is not found"""
    # Mock process iterator with no file watcher
    mock_process = MagicMock()
    mock_process.info = {
        "pid": 9999,
        "name": "python",
        "cmdline": ["python", "-m", "app.server"],
        "create_time": time.time() - 1800,
    }

    current_process = MagicMock()
    current_process.info = {"pid": os.getpid()}

    mock_psutil.process_iter.return_value = [current_process, mock_process]

    with patch("app.services.service_status_service.PSUTIL_AVAILABLE", True):
        result = ServiceStatusService.get_file_watcher_info()

    assert result is None


@patch("app.services.service_status_service.ServiceStatusService.check_service_health")
@patch(
    "app.services.service_status_service.ServiceStatusService.get_current_process_info"
)
def test_check_all_services_includes_process_info(
    mock_get_process_info, mock_check_health
):
    """Test that check_all_services includes process info for wiki service"""
    mock_get_process_info.return_value = {
        "pid": 12345,
        "uptime_seconds": 3600.0,
        "cpu_percent": 2.5,
        "memory_mb": 150.0,
        "memory_percent": 1.2,
        "threads": 8,
        "open_files": 15,
    }

    mock_check_health.return_value = {
        "status": "healthy",
        "response_time_ms": 5.0,
        "error": None,
        "details": {},
    }

    results = ServiceStatusService.check_all_services()

    # Wiki service should have process info
    assert "wiki" in results
    assert "process_info" in results["wiki"]
    assert results["wiki"]["process_info"]["pid"] == 12345

    # Should check all services
    assert len(results) == len(ServiceStatusService.SERVICES)


@patch("app.services.service_status_service.ServiceStatusService.check_service_health")
def test_check_all_services_uses_short_timeout_for_wiki(mock_check_health):
    """Test that wiki service check uses shorter timeout"""
    mock_check_health.return_value = {
        "status": "healthy",
        "response_time_ms": 5.0,
        "error": None,
        "details": {},
    }

    ServiceStatusService.check_all_services()

    # Check that wiki was called with 0.5s timeout
    wiki_calls = [
        call for call in mock_check_health.call_args_list if call[0][0] == "wiki"
    ]
    assert len(wiki_calls) > 0
    # The timeout should be 0.5 for wiki
    assert wiki_calls[0][1]["timeout"] == 0.5


@patch("app.services.service_status_service.ServiceStatusService.check_service_health")
def test_check_all_services_uses_standard_timeout_for_others(mock_check_health):
    """Test that other services use 1.0s timeout"""
    mock_check_health.return_value = {
        "status": "healthy",
        "response_time_ms": 5.0,
        "error": None,
        "details": {},
    }

    ServiceStatusService.check_all_services()

    # Check that non-wiki services were called with 1.0s timeout
    other_calls = [
        call for call in mock_check_health.call_args_list if call[0][0] != "wiki"
    ]
    assert len(other_calls) > 0
    # All should use 1.0s timeout
    for call in other_calls:
        assert call[1]["timeout"] == 1.0
