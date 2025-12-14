"""Test page service"""
import os
import uuid
import tempfile
import shutil
from app.services.page_service import PageService
from app.models.page import Page
from app import db


def test_create_page_basic(app):
    """Test basic page creation"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Test Page",
            content="# Test Page\n\nContent here.",
            user_id=user_id
        )
        
        assert page.title == "Test Page"
        assert page.slug == "test-page"
        assert page.status == "published"
        assert page.word_count > 0
        assert page.content_size_kb > 0
        assert page.created_by == user_id
        assert page.updated_by == user_id


def test_create_page_with_custom_slug(app):
    """Test page creation with custom slug"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Test Page",
            content="Content",
            user_id=user_id,
            slug="custom-slug"
        )
        
        assert page.slug == "custom-slug"


def test_create_page_duplicate_slug(app):
    """Test that duplicate slugs are rejected"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        PageService.create_page(
            title="First Page",
            content="Content",
            user_id=user_id,
            slug="test-slug"
        )
        
        import pytest
        with pytest.raises(ValueError, match="already exists"):
            PageService.create_page(
                title="Second Page",
                content="Content",
                user_id=user_id,
                slug="test-slug"
            )


def test_create_page_with_parent(app):
    """Test page creation with parent"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        parent = PageService.create_page(
            title="Parent Page",
            content="Parent content",
            user_id=user_id
        )
        
        child = PageService.create_page(
            title="Child Page",
            content="Child content",
            user_id=user_id,
            parent_id=parent.id
        )
        
        assert child.parent_id == parent.id
        assert child in parent.children


def test_create_page_draft(app):
    """Test creating a draft page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Draft Page",
            content="Draft content",
            user_id=user_id,
            status="draft"
        )
        
        assert page.status == "draft"


def test_update_page_content(app):
    """Test updating page content"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Test Page",
            content="Original content",
            user_id=user_id
        )
        
        original_version = page.version
        
        updated = PageService.update_page(
            page_id=page.id,
            user_id=user_id,
            content="Updated content"
        )
        
        assert updated.content == "Updated content"
        assert updated.version > original_version


def test_update_page_slug(app):
    """Test updating page slug"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Test Page",
            content="Content",
            user_id=user_id,
            slug="old-slug"
        )
        
        updated = PageService.update_page(
            page_id=page.id,
            user_id=user_id,
            slug="new-slug"
        )
        
        assert updated.slug == "new-slug"


def test_update_page_parent(app):
    """Test updating page parent"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        parent1 = PageService.create_page(
            title="Parent 1",
            content="Content",
            user_id=user_id
        )
        
        parent2 = PageService.create_page(
            title="Parent 2",
            content="Content",
            user_id=user_id
        )
        
        child = PageService.create_page(
            title="Child",
            content="Content",
            user_id=user_id,
            parent_id=parent1.id
        )
        
        updated = PageService.update_page(
            page_id=child.id,
            user_id=user_id,
            parent_id=parent2.id
        )
        
        assert updated.parent_id == parent2.id


def test_update_page_circular_reference(app):
    """Test that circular parent references are prevented"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        parent = PageService.create_page(
            title="Parent",
            content="Content",
            user_id=user_id
        )
        
        child = PageService.create_page(
            title="Child",
            content="Content",
            user_id=user_id,
            parent_id=parent.id
        )
        
        import pytest
        with pytest.raises(ValueError, match="circular"):
            PageService.update_page(
                page_id=parent.id,
                user_id=user_id,
                parent_id=child.id
            )


def test_delete_page(app):
    """Test page deletion"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
            user_id = uuid.uuid4()
            
            page = PageService.create_page(
                title="Test Page",
                content="Content",
                user_id=user_id
            )
            
            result = PageService.delete_page(page.id, user_id)
            
            assert result['deleted_page']['id'] == str(page.id)
            assert Page.query.get(page.id) is None
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_delete_page_with_children(app):
    """Test deleting page with children creates orphans"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
            user_id = uuid.uuid4()
            
            parent = PageService.create_page(
                title="Parent",
                content="Content",
                user_id=user_id
            )
            
            child1 = PageService.create_page(
                title="Child 1",
                content="Content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            child2 = PageService.create_page(
                title="Child 2",
                content="Content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            result = PageService.delete_page(parent.id, user_id)
            
            assert len(result['orphaned_pages']) == 2
            assert any(p['id'] == str(child1.id) for p in result['orphaned_pages'])
            assert any(p['id'] == str(child2.id) for p in result['orphaned_pages'])
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_get_page_draft_visibility(app):
    """Test draft page visibility rules"""
    with app.app_context():
        user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        draft = PageService.create_page(
            title="Draft Page",
            content="Draft content",
            user_id=user_id,
            status="draft"
        )
        
        # Writer who created it can see it
        page = PageService.get_page(draft.id, user_role='writer', user_id=user_id)
        assert page is not None
        
        # Other writer cannot see it
        page = PageService.get_page(draft.id, user_role='writer', user_id=other_user_id)
        assert page is None
        
        # Admin can see it
        page = PageService.get_page(draft.id, user_role='admin')
        assert page is not None
        
        # Viewer cannot see it
        page = PageService.get_page(draft.id, user_role='viewer')
        assert page is None


def test_list_pages_draft_filtering(app):
    """Test list pages with draft filtering"""
    with app.app_context():
        user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        published = PageService.create_page(
            title="Published",
            content="Content",
            user_id=user_id,
            status="published"
        )
        
        my_draft = PageService.create_page(
            title="My Draft",
            content="Content",
            user_id=user_id,
            status="draft"
        )
        
        other_draft = PageService.create_page(
            title="Other Draft",
            content="Content",
            user_id=other_user_id,
            status="draft"
        )
        
        # Viewer sees only published
        pages = PageService.list_pages(user_role='viewer')
        assert len(pages) == 1
        assert pages[0].id == published.id
        
        # Writer sees published + own drafts
        pages = PageService.list_pages(user_role='writer', user_id=user_id)
        assert len(pages) == 2
        assert any(p.id == published.id for p in pages)
        assert any(p.id == my_draft.id for p in pages)
        assert not any(p.id == other_draft.id for p in pages)
        
        # Admin sees all
        pages = PageService.list_pages(user_role='admin', include_drafts=True)
        assert len(pages) == 3


def test_can_edit_permissions(app):
    """Test edit permission checking"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        page = PageService.create_page(
            title="Test Page",
            content="Content",
            user_id=user_id
        )
        
        assert PageService.can_edit(page, 'admin', user_id) == True
        assert PageService.can_edit(page, 'writer', user_id) == True
        assert PageService.can_edit(page, 'player', user_id) == False
        assert PageService.can_edit(page, 'viewer', user_id) == False


def test_can_delete_permissions(app):
    """Test delete permission checking"""
    with app.app_context():
        user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        my_page = PageService.create_page(
            title="My Page",
            content="Content",
            user_id=user_id
        )
        
        other_page = PageService.create_page(
            title="Other Page",
            content="Content",
            user_id=other_user_id
        )
        
        # Admin can delete any page
        assert PageService.can_delete(my_page, 'admin', user_id) == True
        assert PageService.can_delete(other_page, 'admin', user_id) == True
        
        # Writer can delete pages they didn't create
        assert PageService.can_delete(other_page, 'writer', user_id) == True
        assert PageService.can_delete(my_page, 'writer', user_id) == False
        
        # Others cannot delete
        assert PageService.can_delete(my_page, 'player', user_id) == False
        assert PageService.can_delete(my_page, 'viewer', user_id) == False

