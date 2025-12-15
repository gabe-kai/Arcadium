"""Tests for page CRUD endpoints"""
import uuid
import pytest
from app import db
from app.models.page import Page
# Import app and client from parent conftest
from tests.conftest import app, client
# Import API-specific fixtures and helpers
from tests.test_api.conftest import (
    test_user_id, test_writer_id, test_admin_id,
    test_page, test_draft_page, mock_auth, auth_headers
)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'wiki'


def test_list_pages_empty(client):
    """Test listing pages when none exist"""
    response = client.get('/api/pages')
    assert response.status_code == 200
    data = response.get_json()
    assert data['pages'] == []
    assert data['total'] == 0


def test_list_pages_with_page(client, test_page):
    """Test listing pages with existing page"""
    response = client.get('/api/pages')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['pages']) >= 1
    # Find our test page
    page_data = next((p for p in data['pages'] if p['slug'] == 'test-page'), None)
    assert page_data is not None
    assert page_data['title'] == 'Test Page'


def test_list_pages_with_filters(client, test_page):
    """Test listing pages with filters"""
    # Test filtering by section
    response = client.get('/api/pages?section=test')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data['pages'], list)
    
    # Test pagination
    response = client.get('/api/pages?limit=10&offset=0')
    assert response.status_code == 200
    data = response.get_json()
    assert 'limit' in data
    assert 'offset' in data


def test_get_page(client, test_page):
    """Test getting a single page"""
    page_id = str(test_page.id)
    response = client.get(f'/api/pages/{page_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Test Page'
    assert data['slug'] == 'test-page'
    assert 'content' in data
    assert 'html_content' in data
    assert 'table_of_contents' in data
    assert 'forward_links' in data
    assert 'backlinks' in data


def test_get_page_not_found(client):
    """Test getting a non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f'/api/pages/{fake_id}')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_get_page_draft_visibility(client, test_draft_page, test_user_id):
    """Test that draft pages are hidden from non-creators"""
    page_id = str(test_draft_page.id)
    
    # As viewer (no auth), should get 404
    response = client.get(f'/api/pages/{page_id}')
    assert response.status_code == 404
    
    # As creator, should be able to see it
    with mock_auth(test_user_id, 'writer'):
        response = client.get(f'/api/pages/{page_id}', headers=auth_headers(test_user_id, 'writer'))
        assert response.status_code == 200


def test_create_page_requires_auth(client):
    """Test that creating a page requires authentication"""
    response = client.post('/api/pages', json={
        'title': 'New Page',
        'content': '# Content'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_create_page_success(client, app, test_writer_id):
    """Test successfully creating a page"""
    with mock_auth(test_writer_id, 'writer'):
        response = client.post('/api/pages', 
            json={
                'title': 'New Page',
                'content': '# Content',
                'status': 'published'
            },
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == 'New Page'
        assert 'id' in data
        assert 'slug' in data


def test_create_page_missing_title(client, test_writer_id):
    """Test creating page without title"""
    with mock_auth(test_writer_id, 'writer'):
        response = client.post('/api/pages',
            json={'content': '# Content'},
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


def test_create_page_viewer_forbidden(client, test_user_id):
    """Test that viewers cannot create pages"""
    with mock_auth(test_user_id, 'viewer'):
        response = client.post('/api/pages',
            json={'title': 'New Page', 'content': '# Content'},
            headers=auth_headers(test_user_id, 'viewer')
        )
        assert response.status_code == 403


def test_update_page_requires_auth(client, test_page):
    """Test that updating a page requires authentication"""
    page_id = str(test_page.id)
    response = client.put(f'/api/pages/{page_id}', json={
        'title': 'Updated Title'
    })
    assert response.status_code == 401


def test_update_page_success(client, app, test_writer_id):
    """Test successfully updating a page"""
    # Create a page owned by the writer
    with app.app_context():
        page = Page(
            title="Page to Update",
            slug="page-to-update",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status='published',
            file_path="page-to-update.md"
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)
    
    with mock_auth(test_writer_id, 'writer'):
        response = client.put(f'/api/pages/{page_id}',
            json={'title': 'Updated Title'},
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['title'] == 'Updated Title'


def test_update_page_wrong_owner(client, app, test_page, test_writer_id, test_user_id):
    """Test that writers cannot update pages they didn't create"""
    # Page is created by test_user_id, but we're trying to update as test_writer_id
    with mock_auth(test_writer_id, 'writer'):
        page_id = str(test_page.id)
        response = client.put(f'/api/pages/{page_id}',
            json={'title': 'Updated Title'},
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 403


def test_update_page_admin_can_edit_any(client, test_page, test_admin_id):
    """Test that admins can update any page"""
    with mock_auth(test_admin_id, 'admin'):
        page_id = str(test_page.id)
        response = client.put(f'/api/pages/{page_id}',
            json={'title': 'Admin Updated Title'},
            headers=auth_headers(test_admin_id, 'admin')
        )
        assert response.status_code == 200


def test_delete_page_requires_auth(client, test_page):
    """Test that deleting a page requires authentication"""
    page_id = str(test_page.id)
    response = client.delete(f'/api/pages/{page_id}')
    assert response.status_code == 401


def test_delete_page_success(client, app, test_writer_id):
    """Test successfully deleting a page"""
    # Create a page owned by the writer
    with app.app_context():
        page = Page(
            title="Page to Delete",
            slug="page-to-delete",
            content="# Content",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status='published',
            file_path="page-to-delete.md"
        )
        db.session.add(page)
        db.session.commit()
        page_id = str(page.id)
    
    with mock_auth(test_writer_id, 'writer'):
        response = client.delete(f'/api/pages/{page_id}',
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data


def test_delete_page_with_children(client, app, test_writer_id):
    """Test deleting a page with children moves them to orphanage"""
    with app.app_context():
        # Create parent page
        parent = Page(
            title="Parent Page",
            slug="parent-page",
            content="# Parent",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status='published',
            file_path="parent-page.md"
        )
        db.session.add(parent)
        db.session.flush()
        
        # Create child page
        child = Page(
            title="Child Page",
            slug="child-page",
            content="# Child",
            created_by=test_writer_id,
            updated_by=test_writer_id,
            status='published',
            parent_id=parent.id,
            file_path="child-page.md"
        )
        db.session.add(child)
        db.session.commit()
        parent_id = str(parent.id)
    
    with mock_auth(test_writer_id, 'writer'):
        response = client.delete(f'/api/pages/{parent_id}',
            headers=auth_headers(test_writer_id, 'writer')
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'orphaned_pages' in data
        # Check that we have at least one orphaned page
        # Note: orphaned_count might be 0 if OrphanageService fails silently
        # but orphaned_pages should still be in the response
        assert len(data.get('orphaned_pages', [])) >= 1, f"Expected at least 1 orphaned page, got {data.get('orphaned_count', 0)}. Response: {data}"
        assert data['orphaned_count'] >= 1
