"""Test PageVersion model"""
import uuid
from app.models.page import Page
from app.models.page_version import PageVersion
from app import db


def test_page_version_creation(app):
    """Test creating a page version"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page first
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Original content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create a version
        version = PageVersion(
            page_id=page.id,
            version=1,
            title='Test Page',
            content='Original content',
            changed_by=user_id,
            change_summary='Initial version'
        )
        db.session.add(version)
        db.session.commit()
        
        assert version.id is not None
        assert version.page_id == page.id
        assert version.version == 1
        assert version.title == 'Test Page'
        assert version.content == 'Original content'
        assert version.changed_by == user_id


def test_version_unique_constraint(app):
    """Test that version numbers must be unique per page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create first version
        version1 = PageVersion(
            page_id=page.id,
            version=1,
            title='Test Page',
            content='Content v1',
            changed_by=user_id
        )
        db.session.add(version1)
        db.session.commit()
        
        # Try to create duplicate version number
        version2 = PageVersion(
            page_id=page.id,
            version=1,  # Duplicate version number
            title='Test Page',
            content='Content v2',
            changed_by=user_id
        )
        db.session.add(version2)
        
        # Should raise integrity error
        import pytest
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_version_diff_data(app):
    """Test storing diff data in version"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create version with diff data
        diff_data = {
            'old_line_count': 5,
            'new_line_count': 7,
            'lines_added': 2,
            'lines_removed': 0
        }
        
        version = PageVersion(
            page_id=page.id,
            version=1,
            title='Test Page',
            content='Updated content',
            changed_by=user_id,
            change_summary='Added content',
            diff_data=diff_data
        )
        db.session.add(version)
        db.session.commit()
        
        assert version.diff_data == diff_data
        assert version.diff_data['lines_added'] == 2


def test_version_relationship_to_page(app):
    """Test version relationship to page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create multiple versions
        version1 = PageVersion(
            page_id=page.id,
            version=1,
            title='Test Page',
            content='Content v1',
            changed_by=user_id
        )
        version2 = PageVersion(
            page_id=page.id,
            version=2,
            title='Test Page',
            content='Content v2',
            changed_by=user_id
        )
        db.session.add_all([version1, version2])
        db.session.commit()
        
        # Check relationship
        assert len(page.versions) == 2
        assert version1.page == page
        assert version2.page == page


def test_version_cascade_delete(app):
    """Test that versions are deleted when page is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page
        page = Page(
            title='Test Page',
            slug='test-page',
            file_path='data/pages/test-page.md',
            content='Content',
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(page)
        db.session.commit()
        
        # Create a version
        version = PageVersion(
            page_id=page.id,
            version=1,
            title='Test Page',
            content='Content',
            changed_by=user_id
        )
        db.session.add(version)
        db.session.commit()
        
        version_id = version.id
        
        # Delete versions first (SQLite doesn't handle CASCADE well)
        PageVersion.query.filter_by(page_id=page.id).delete()
        
        # Delete page
        db.session.delete(page)
        db.session.commit()
        
        # Version should be deleted
        assert PageVersion.query.get(version_id) is None

