"""Tests for service status service"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests
from app import db
from app.models.page import Page
from app.models.wiki_config import WikiConfig
from app.services.service_status_service import ServiceStatusService


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_get_status_indicator():
    """Test status indicator emoji"""
    assert ServiceStatusService.get_status_indicator("healthy") == "🟢"
    assert ServiceStatusService.get_status_indicator("degraded") == "🟡"
    assert ServiceStatusService.get_status_indicator("unhealthy") == "🔴"
    assert ServiceStatusService.get_status_indicator("unknown") == "⚪"


def test_get_status_display_name():
    """Test status display name"""
    assert ServiceStatusService.get_status_display_name("healthy") == "Healthy"
    assert ServiceStatusService.get_status_display_name("degraded") == "Degraded"
    assert ServiceStatusService.get_status_display_name("unhealthy") == "Unhealthy"
    assert ServiceStatusService.get_status_display_name("unknown") == "Unknown"


def test_check_service_health_healthy():
    """Test checking a healthy service"""
    # Create a mock session and set it directly
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "healthy",
        "service": "wiki",
        "version": "1.0.0",
    }
    mock_response.headers.get.return_value = "application/json"
    mock_session.get.return_value = mock_response

    # Set the session directly
    original_session = ServiceStatusService._session
    ServiceStatusService._session = mock_session

    try:
        # Mock time to simulate fast response
        with patch("app.services.service_status_service.time.time") as mock_time:
            mock_time.side_effect = [0.0, 0.1]  # 100ms elapsed
            result = ServiceStatusService.check_service_health("wiki", timeout=2.0)

        assert result["status"] == "healthy"
        assert result["error"] is None
        assert "response_time_ms" in result
        assert result["details"]["service"] == "wiki"
    finally:
        # Restore original session
        ServiceStatusService._session = original_session


def test_check_service_health_degraded():
    """Test checking a degraded service"""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "degraded",
        "service": "notification",
        "warnings": ["High latency"],
    }
    mock_response.headers.get.return_value = "application/json"
    mock_session.get.return_value = mock_response

    original_session = ServiceStatusService._session
    ServiceStatusService._session = mock_session

    try:
        with patch("app.services.service_status_service.time.time") as mock_time:
            mock_time.side_effect = [0.0, 0.1]
            result = ServiceStatusService.check_service_health(
                "notification", timeout=2.0
            )

        assert result["status"] == "degraded"
        assert result["error"] is None
    finally:
        ServiceStatusService._session = original_session


def test_check_service_health_timeout():
    """Test checking a service that times out"""
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.Timeout()

    original_session = ServiceStatusService._session
    ServiceStatusService._session = mock_session

    try:
        result = ServiceStatusService.check_service_health("auth", timeout=1.0)

        assert result["status"] == "unhealthy"
        assert result["error"] == "Request timeout"
        assert result["response_time_ms"] == 1000.0  # timeout * 1000
    finally:
        ServiceStatusService._session = original_session


def test_check_service_health_connection_error():
    """Test checking a service that can't connect"""
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.ConnectionError()

    original_session = ServiceStatusService._session
    ServiceStatusService._session = mock_session

    try:
        result = ServiceStatusService.check_service_health("game-server")

        assert result["status"] == "unhealthy"
        assert result["error"] == "Connection refused"
    finally:
        ServiceStatusService._session = original_session


def test_check_service_health_non_200():
    """Test checking a service that returns non-200"""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_session.get.return_value = mock_response

    original_session = ServiceStatusService._session
    ServiceStatusService._session = mock_session

    try:
        result = ServiceStatusService.check_service_health("auth")

        assert result["status"] == "unhealthy"
        assert "HTTP 500" in result["error"]
    finally:
        ServiceStatusService._session = original_session


def test_check_service_health_unknown_service():
    """Test checking an unknown service"""
    result = ServiceStatusService.check_service_health("unknown-service")

    assert result["status"] == "unhealthy"
    assert "Unknown service" in result["error"]


@patch("app.services.service_status_service.ServiceStatusService.check_service_health")
def test_check_all_services(mock_check):
    """Test checking all services"""
    mock_check.return_value = {
        "status": "healthy",
        "response_time_ms": 10.0,
        "error": None,
        "details": {},
    }

    results = ServiceStatusService.check_all_services()

    # Should check all defined services
    assert len(results) == len(ServiceStatusService.SERVICES)
    assert "wiki" in results
    assert "auth" in results
    assert "notification" in results


def test_get_service_status_page_not_found(app):
    """Test getting status page when it doesn't exist"""
    with app.app_context():
        db.session.query(Page).filter_by(slug="service-status").delete()
        db.session.commit()

        page = ServiceStatusService.get_service_status_page()
        assert page is None


def test_get_service_status_page_exists(app, test_user_id):
    """Test getting status page when it exists"""
    with app.app_context():
        # Create status page
        page = Page(
            title="Arcadium Service Status",
            slug="service-status",
            content="# Service Status",
            created_by=test_user_id,
            updated_by=test_user_id,
            is_system_page=True,
            status="published",
            file_path="service-status.md",
        )
        db.session.add(page)
        db.session.commit()

        found = ServiceStatusService.get_service_status_page()
        assert found is not None
        assert found.slug == "service-status"
        assert found.is_system_page is True


@patch("app.services.service_status_service.ServiceStatusService.check_all_services")
def test_create_or_update_status_page_create(mock_check_all, app, test_user_id):
    """Test creating the status page"""
    with app.app_context():
        # Clear existing page
        db.session.query(Page).filter_by(slug="service-status").delete()
        db.session.commit()

        # Mock service checks
        mock_check_all.return_value = {
            "wiki": {
                "status": "healthy",
                "response_time_ms": 5.0,
                "error": None,
                "details": {},
            },
            "auth": {
                "status": "healthy",
                "response_time_ms": 12.0,
                "error": None,
                "details": {},
            },
            "notification": {
                "status": "degraded",
                "response_time_ms": 250.0,
                "error": "High latency",
                "details": {},
            },
        }

        page = ServiceStatusService.create_or_update_status_page(
            test_user_id, mock_check_all.return_value
        )

        assert page is not None
        assert page.slug == "service-status"
        assert page.is_system_page is True
        assert page.title == "Arcadium Service Status"
        assert "Wiki Service" in page.content
        assert "Auth Service" in page.content
        assert "🟢" in page.content
        assert "🟡" in page.content


@patch("app.services.service_status_service.ServiceStatusService.check_all_services")
def test_create_or_update_status_page_update(mock_check_all, app, test_user_id):
    """Test updating existing status page"""
    with app.app_context():
        # Create existing page
        existing = Page(
            title="Arcadium Service Status",
            slug="service-status",
            content="# Old Content",
            created_by=test_user_id,
            updated_by=test_user_id,
            is_system_page=True,
            status="published",
            file_path="service-status.md",
        )
        db.session.add(existing)
        db.session.commit()

        # Mock service checks
        mock_check_all.return_value = {
            "wiki": {
                "status": "healthy",
                "response_time_ms": 5.0,
                "error": None,
                "details": {},
            }
        }

        page = ServiceStatusService.create_or_update_status_page(
            test_user_id, mock_check_all.return_value
        )

        assert page.id == existing.id
        assert page.content != "# Old Content"
        assert "Wiki Service" in page.content


def test_get_manual_status_notes_empty(app):
    """Test getting manual notes when none exist"""
    with app.app_context():
        notes = ServiceStatusService.get_manual_status_notes()
        assert notes == {}


def test_get_manual_status_notes_with_data(app, test_user_id):
    """Test getting manual notes"""
    with app.app_context():
        import json

        config = WikiConfig(
            key="service_status_notes_auth",
            value=json.dumps({"issue": "Maintenance", "eta": "2024-01-01T12:00:00Z"}),
            updated_by=test_user_id,
        )
        db.session.add(config)
        db.session.commit()

        notes = ServiceStatusService.get_manual_status_notes()
        assert "auth" in notes
        assert notes["auth"]["issue"] == "Maintenance"


def test_set_manual_status_notes(app, test_user_id):
    """Test setting manual notes"""
    with app.app_context():
        notes_data = {
            "issue": "Planned maintenance",
            "impact": "Service unavailable",
            "eta": "2024-01-01T14:00:00Z",
        }

        ServiceStatusService.set_manual_status_notes("auth", notes_data, test_user_id)

        config = (
            db.session.query(WikiConfig)
            .filter_by(key="service_status_notes_auth")
            .first()
        )
        assert config is not None

        import json

        stored_data = json.loads(config.value)
        assert stored_data["issue"] == "Planned maintenance"


def test_set_manual_status_notes_updates_existing(app, test_user_id):
    """Test updating existing manual notes"""
    with app.app_context():
        import json

        # Create initial notes
        config = WikiConfig(
            key="service_status_notes_auth",
            value=json.dumps({"issue": "Old issue"}),
            updated_by=test_user_id,
        )
        db.session.add(config)
        db.session.commit()

        # Update notes
        new_notes = {"issue": "New issue", "eta": "2024-01-01T12:00:00Z"}
        ServiceStatusService.set_manual_status_notes("auth", new_notes, test_user_id)

        # Verify update
        db.session.refresh(config)
        stored_data = json.loads(config.value)
        assert stored_data["issue"] == "New issue"
