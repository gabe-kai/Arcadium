"""Tests for admin dashboard and configuration endpoints."""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app import db
from app.models.page import Page
from app.models.comment import Comment
from app.models.wiki_config import WikiConfig
from app.models.oversized_page_notification import OversizedPageNotification
from tests.test_api.conftest import mock_auth, auth_headers, test_admin_id, test_writer_id


def _create_page(app, user_id, size_kb=10.0, word_count=100, title="Test Page", slug="test-page"):
    """Helper to create a page inside app context."""
    with app.app_context():
        page = Page(
            title=title,
            slug=slug,
            content="# Content",
            created_by=user_id,
            updated_by=user_id,
            content_size_kb=size_kb,
            word_count=word_count,
            file_path=f"{slug}.md",
        )
        db.session.add(page)
        db.session.commit()
        return page.id


def test_admin_endpoints_require_auth(client):
    """All admin endpoints should require authentication."""
    resp = client.get("/api/admin/dashboard/stats")
    assert resp.status_code == 401

    resp = client.get("/api/admin/dashboard/size-distribution")
    assert resp.status_code == 401

    resp = client.post("/api/admin/config/upload-size", json={"max_size_mb": 10})
    assert resp.status_code == 401

    resp = client.post(
        "/api/admin/config/page-size",
        json={"max_size_kb": 500, "resolution_due_date": "2024-02-01T00:00:00Z"},
    )
    assert resp.status_code == 401


def test_admin_endpoints_require_admin_role(client, app, test_writer_id):
    """Non-admin users should receive 403 on admin endpoints."""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.get("/api/admin/dashboard/stats", headers=headers)
        assert resp.status_code == 403

        resp = client.get("/api/admin/dashboard/size-distribution", headers=headers)
        assert resp.status_code == 403


def test_get_dashboard_stats_basic(client, app, test_admin_id):
    """Dashboard stats should return counts for pages and comments."""
    user_id = test_admin_id
    with app.app_context():
        # Create pages
        page1 = Page(
            title="Page 1",
            slug="page-1",
            content="# One",
            created_by=user_id,
            updated_by=user_id,
            content_size_kb=10.0,
            word_count=100,
            section="rules",
            file_path="page-1.md",
        )
        page2 = Page(
            title="Page 2",
            slug="page-2",
            content="# Two",
            created_by=user_id,
            updated_by=user_id,
            content_size_kb=20.0,
            word_count=200,
            section="lore",
            file_path="page-2.md",
        )
        db.session.add(page1)
        db.session.add(page2)
        db.session.flush()

        # Create comments
        comment = Comment(
            page_id=page1.id,
            user_id=user_id,
            content="Test comment",
            is_recommendation=False,
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/dashboard/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_pages"] == 2
        assert data["total_sections"] == 2  # rules, lore
        assert data["total_comments"] == 1
        assert "storage_usage_mb" in data
        assert "total_users" in data
        assert "recent_activity" in data


def test_get_size_distribution_buckets(client, app, test_admin_id):
    """Size distribution should bucket pages by size and word count."""
    user_id = test_admin_id
    with app.app_context():
        # Clear pages to control counts
        db.session.query(Page).delete()
        db.session.commit()

        # Create pages to hit several buckets
        _create_page(app, user_id, size_kb=5.0, word_count=100, title="Small", slug="small")
        _create_page(app, user_id, size_kb=20.0, word_count=800, title="Medium", slug="medium")
        _create_page(app, user_id, size_kb=60.0, word_count=1500, title="Large", slug="large")
        _create_page(app, user_id, size_kb=200.0, word_count=3000, title="XL", slug="xl")

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/dashboard/size-distribution", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "by_size_kb" in data
        assert "by_word_count" in data

        # Ensure total counts match number of pages created
        total_size_count = sum(data["by_size_kb"].values())
        total_word_count = sum(data["by_word_count"].values())
        assert total_size_count == 4
        assert total_word_count == 4


def test_configure_upload_size_success(client, app, test_admin_id):
    """Configure upload size should store WikiConfig and return new value."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/upload-size",
            json={"max_size_mb": 15, "is_custom": True},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["max_size_mb"] == 15
        assert "updated_at" in data

    with app.app_context():
        cfg = db.session.query(WikiConfig).filter_by(key="upload_max_size_mb").first()
        assert cfg is not None
        assert float(cfg.value) == 15.0


def test_configure_page_size_success(client, app, test_admin_id):
    """Configure page size should return oversized_pages_count and create notifications."""
    user_id = test_admin_id
    with app.app_context():
        # Clear existing pages and notifications
        db.session.query(OversizedPageNotification).delete()
        db.session.query(Page).delete()
        db.session.commit()

        # One within threshold, one above
        small_page_id = _create_page(app, user_id, size_kb=100.0, word_count=1000, title="Small", slug="small-thresh")
        big_page_id = _create_page(app, user_id, size_kb=600.0, word_count=2000, title="Big", slug="big-thresh")

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/page-size",
            json={
                "max_size_kb": 500,
                "resolution_due_date": "2024-02-01T00:00:00Z",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["max_size_kb"] == 500
        assert data["oversized_pages_count"] == 1  # Only the 600kb page
        assert data["notifications_created"] == 1  # One notification created

    # Verify notification was created
    with app.app_context():
        notifications = db.session.query(OversizedPageNotification).filter_by(
            resolved=False
        ).all()
        assert len(notifications) == 1
        assert notifications[0].page_id == big_page_id
        assert notifications[0].max_size_kb == 500.0
        assert notifications[0].current_size_kb == 600.0
        
        # Verify small page has no notification
        small_notif = db.session.query(OversizedPageNotification).filter_by(
            page_id=small_page_id
        ).first()
        assert small_notif is None


def test_get_oversized_pages_and_update_status(client, app, test_admin_id):
    """Get oversized pages and update their status."""
    user_id = test_admin_id
    with app.app_context():
        # Create a page
        page = Page(
            title="Oversized",
            slug="oversized",
            content="# Oversized",
            created_by=user_id,
            updated_by=user_id,
            content_size_kb=800.0,
            word_count=6000,
            file_path="oversized.md",
        )
        db.session.add(page)
        db.session.flush()

        # Create notification
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        notif = OversizedPageNotification(
            page_id=page.id,
            current_size_kb=800.0,
            max_size_kb=500.0,
            resolution_due_date=due_date,
            notified_users=[],
            resolved=False,
        )
        db.session.add(notif)
        db.session.commit()
        page_id_str = str(page.id)

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")

        # Get oversized pages list
        resp = client.get("/api/admin/oversized-pages", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pages" in data
        assert len(data["pages"]) == 1
        page_info = data["pages"][0]
        assert page_info["id"] == page_id_str
        assert page_info["status"] == "pending"

        # Update status to resolved and extend due date
        new_due = (datetime.now(timezone.utc) + timedelta(days=14)).replace(microsecond=0)
        new_due_iso = new_due.isoformat().replace("+00:00", "Z")

        resp = client.put(
            f"/api/admin/oversized-pages/{page_id_str}/status",
            json={"status": "resolved", "extend_due_date": new_due_iso},
            headers=headers,
        )
        assert resp.status_code == 200
        updated = resp.get_json()
        assert updated["page_id"] == page_id_str
        assert updated["status"] == "resolved"
        assert updated["resolved"] is True
        assert updated["due_date"] is not None


def test_get_service_status_requires_auth(client):
    """Service status endpoint should require authentication"""
    resp = client.get("/api/admin/service-status")
    assert resp.status_code == 401


def test_get_service_status_requires_admin(client, app, test_writer_id):
    """Service status endpoint should require admin role"""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.get("/api/admin/service-status", headers=headers)
        assert resp.status_code == 403


@patch('app.routes.admin_routes.ServiceStatusService.check_all_services')
def test_get_service_status_success(mock_check_all, client, app, test_admin_id):
    """Get service status should return status for all services"""
    # Mock service checks
    mock_check_all.return_value = {
        'wiki': {'status': 'healthy', 'response_time_ms': 5.0, 'error': None, 'details': {'service': 'wiki'}},
        'auth': {'status': 'healthy', 'response_time_ms': 12.0, 'error': None, 'details': {'service': 'auth'}},
        'notification': {'status': 'degraded', 'response_time_ms': 250.0, 'error': 'High latency', 'details': {}}
    }
    
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.get("/api/admin/service-status", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "services" in data
        assert "last_updated" in data
        assert "wiki" in data["services"]
        assert data["services"]["wiki"]["status"] == "healthy"
        assert data["services"]["notification"]["status"] == "degraded"


def test_update_service_status_requires_auth(client):
    """Update service status should require authentication"""
    resp = client.put("/api/admin/service-status", json={"service": "auth", "notes": {}})
    assert resp.status_code == 401


def test_update_service_status_requires_admin(client, app, test_writer_id):
    """Update service status should require admin role"""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.put("/api/admin/service-status", json={"service": "auth", "notes": {}}, headers=headers)
        assert resp.status_code == 403


def test_update_service_status_missing_service(client, app, test_admin_id):
    """Update service status should return 400 if service is missing"""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.put("/api/admin/service-status", json={"notes": {}}, headers=headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "service" in data["error"].lower()


def test_update_service_status_unknown_service(client, app, test_admin_id):
    """Update service status should return 400 if service is unknown"""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.put("/api/admin/service-status", json={"service": "unknown", "notes": {}}, headers=headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "unknown" in data["error"].lower()


def test_update_service_status_success(client, app, test_admin_id):
    """Update service status should set manual notes"""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        notes = {
            "issue": "Planned maintenance",
            "impact": "Service unavailable",
            "eta": "2024-01-01T14:00:00Z"
        }
        resp = client.put(
            "/api/admin/service-status",
            json={"service": "auth", "notes": notes},
            headers=headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["service"] == "auth"
        assert "updated_at" in data
    
    # Verify notes were stored
    with app.app_context():
        import json
        from app.models.wiki_config import WikiConfig
        config = db.session.query(WikiConfig).filter_by(key="service_status_notes_auth").first()
        assert config is not None
        stored_notes = json.loads(config.value)
        assert stored_notes["issue"] == "Planned maintenance"


def test_refresh_service_status_page_requires_auth(client):
    """Refresh service status page should require authentication"""
    resp = client.post("/api/admin/service-status/refresh")
    assert resp.status_code == 401


def test_refresh_service_status_page_requires_admin(client, app, test_writer_id):
    """Refresh service status page should require admin role"""
    with mock_auth(test_writer_id, "writer"):
        headers = auth_headers(test_writer_id, "writer")
        resp = client.post("/api/admin/service-status/refresh", headers=headers)
        assert resp.status_code == 403


@patch('app.services.service_status_service.requests.get')
def test_refresh_service_status_page_success(mock_get, client, app, test_admin_id):
    """Refresh service status page should create or update the page"""
    from app.models.page import Page
    
    # Mock health check responses (most will fail, but that's OK for testing)
    def mock_get_side_effect(url, timeout=None):
        mock_response = MagicMock()
        if 'wiki' in url or 'localhost:5000' in url:
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy', 'service': 'wiki'}
        else:
            # Other services will fail (connection error)
            raise requests.exceptions.ConnectionError()
        return mock_response
    
    mock_get.side_effect = mock_get_side_effect
    
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post("/api/admin/service-status/refresh", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["page_slug"] == "service-status"
        assert "updated_at" in data
    
    # Verify page was created/updated
    with app.app_context():
        page = db.session.query(Page).filter_by(slug='service-status').first()
        assert page is not None
        assert page.is_system_page is True
        assert 'Arcadium Service Status' in page.content


def test_configure_upload_size_missing_field(client, app, test_admin_id):
    """Configure upload size should return 400 if max_size_mb is missing."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/upload-size",
            json={"is_custom": True},
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "max_size_mb" in data["error"].lower()


def test_configure_upload_size_invalid_value(client, app, test_admin_id):
    """Configure upload size should return 400 if max_size_mb is not a number."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/upload-size",
            json={"max_size_mb": "not-a-number", "is_custom": False},
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "number" in data["error"].lower()


def test_configure_upload_size_negative_value(client, app, test_admin_id):
    """Configure upload size should accept negative values (validation handled elsewhere)."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/upload-size",
            json={"max_size_mb": -5, "is_custom": False},
            headers=headers,
        )
        # Currently accepts negative, but stores it
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["max_size_mb"] == -5


def test_configure_upload_size_updates_existing(client, app, test_admin_id):
    """Configure upload size should update existing config."""
    with app.app_context():
        # Create initial config
        config = WikiConfig(
            key="upload_max_size_mb",
            value="10.0",
            updated_by=test_admin_id
        )
        db.session.add(config)
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/upload-size",
            json={"max_size_mb": 20, "is_custom": True},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["max_size_mb"] == 20

    with app.app_context():
        config = db.session.query(WikiConfig).filter_by(key="upload_max_size_mb").first()
        assert config is not None
        assert float(config.value) == 20.0


def test_configure_page_size_missing_fields(client, app, test_admin_id):
    """Configure page size should return 400 if required fields are missing."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        
        # Missing max_size_kb
        resp = client.post(
            "/api/admin/config/page-size",
            json={"resolution_due_date": "2024-02-01T00:00:00Z"},
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "max_size_kb" in data["error"].lower()
        
        # Missing resolution_due_date
        resp = client.post(
            "/api/admin/config/page-size",
            json={"max_size_kb": 500},
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "resolution_due_date" in data["error"].lower()


def test_configure_page_size_invalid_max_size(client, app, test_admin_id):
    """Configure page size should return 400 if max_size_kb is not a number."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/page-size",
            json={
                "max_size_kb": "not-a-number",
                "resolution_due_date": "2024-02-01T00:00:00Z",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "number" in data["error"].lower()


def test_configure_page_size_invalid_date_format(client, app, test_admin_id):
    """Configure page size should return 400 if resolution_due_date is invalid."""
    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/page-size",
            json={
                "max_size_kb": 500,
                "resolution_due_date": "not-a-date",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "iso" in data["error"].lower() or "datetime" in data["error"].lower()


def test_configure_page_size_creates_multiple_notifications(client, app, test_admin_id):
    """Configure page size should create notifications for all oversized pages."""
    user_id = test_admin_id
    with app.app_context():
        # Clear existing pages and notifications
        db.session.query(OversizedPageNotification).delete()
        db.session.query(Page).delete()
        db.session.commit()

        # Create multiple oversized pages
        page1_id = _create_page(app, user_id, size_kb=600.0, word_count=2000, title="Big 1", slug="big-1")
        page2_id = _create_page(app, user_id, size_kb=700.0, word_count=3000, title="Big 2", slug="big-2")
        page3_id = _create_page(app, user_id, size_kb=800.0, word_count=4000, title="Big 3", slug="big-3")
        _create_page(app, user_id, size_kb=100.0, word_count=500, title="Small", slug="small")  # Under limit

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        resp = client.post(
            "/api/admin/config/page-size",
            json={
                "max_size_kb": 500,
                "resolution_due_date": "2024-02-01T00:00:00Z",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["oversized_pages_count"] == 3
        assert data["notifications_created"] == 3

    # Verify all notifications were created
    with app.app_context():
        notifications = db.session.query(OversizedPageNotification).filter_by(
            resolved=False
        ).all()
        assert len(notifications) == 3
        
        page_ids = {notif.page_id for notif in notifications}
        assert page1_id in page_ids
        assert page2_id in page_ids
        assert page3_id in page_ids


def test_configure_page_size_updates_existing_notifications(client, app, test_admin_id):
    """Configure page size should update existing notifications if they already exist."""
    user_id = test_admin_id
    with app.app_context():
        # Clear existing pages and notifications
        db.session.query(OversizedPageNotification).delete()
        db.session.query(Page).delete()
        db.session.commit()

        # Create oversized page
        page_id = _create_page(app, user_id, size_kb=600.0, word_count=2000, title="Big", slug="big")
        
        # Create initial notification
        due_date1 = datetime.now(timezone.utc) + timedelta(days=7)
        notif = OversizedPageNotification(
            page_id=page_id,
            current_size_kb=600.0,
            max_size_kb=500.0,
            resolution_due_date=due_date1,
            notified_users=[],
            resolved=False
        )
        db.session.add(notif)
        db.session.commit()
        
        # Update page size
        page = db.session.query(Page).filter_by(id=page_id).first()
        page.content_size_kb = 700.0
        db.session.commit()

    with mock_auth(test_admin_id, "admin"):
        headers = auth_headers(test_admin_id, "admin")
        due_date2 = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat().replace("+00:00", "Z")
        resp = client.post(
            "/api/admin/config/page-size",
            json={
                "max_size_kb": 500,
                "resolution_due_date": due_date2,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["notifications_created"] == 1

    # Verify notification was updated, not duplicated
    with app.app_context():
        notifications = db.session.query(OversizedPageNotification).filter_by(
            page_id=page_id,
            resolved=False
        ).all()
        assert len(notifications) == 1  # Should be updated, not duplicated
        assert notifications[0].current_size_kb == 700.0  # Updated size
        assert notifications[0].max_size_kb == 500.0


