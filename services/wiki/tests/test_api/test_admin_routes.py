"""Tests for admin dashboard and configuration endpoints."""
import uuid
from datetime import datetime, timezone, timedelta

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
    """Configure page size should return oversized_pages_count."""
    user_id = test_admin_id
    with app.app_context():
        # Clear existing pages
        db.session.query(Page).delete()
        db.session.commit()

        # One within threshold, one above
        _create_page(app, user_id, size_kb=100.0, word_count=1000, title="Small", slug="small-thresh")
        _create_page(app, user_id, size_kb=600.0, word_count=2000, title="Big", slug="big-thresh")

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


