"""Test Comment model"""
import uuid
from app.models.comment import Comment
from app.models.page import Page
from app import db


def test_comment_creation(app):
    """Test creating a comment"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create a page first
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
        
        # Create a comment
        comment = Comment(
            page_id=page.id,
            user_id=user_id,
            content='This is a comment',
            is_recommendation=False
        )
        db.session.add(comment)
        db.session.commit()
        
        assert comment.id is not None
        assert comment.page_id == page.id
        assert comment.thread_depth == 1
        assert comment.is_recommendation == False


def test_thread_depth_calculation(app):
    """Test thread depth calculation"""
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
        
        # Create top-level comment
        comment1 = Comment(
            page_id=page.id,
            user_id=user_id,
            content='Top level',
            thread_depth=1
        )
        db.session.add(comment1)
        db.session.commit()
        
        # Create reply (depth 2)
        comment2 = Comment(
            page_id=page.id,
            parent_comment_id=comment1.id,
            user_id=user_id,
            content='Reply',
            thread_depth=2
        )
        db.session.add(comment2)
        db.session.commit()
        
        assert comment2.thread_depth == 2
        assert comment2.parent_comment_id == comment1.id


def test_max_depth_enforcement(app):
    """Test that maximum depth (5) is enforced"""
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
        
        # Try to create comment with depth > 5
        comment = Comment(
            page_id=page.id,
            user_id=user_id,
            content='Too deep',
            thread_depth=6  # Exceeds max
        )
        db.session.add(comment)
        
        # Should raise constraint violation
        import pytest
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_recommendation_flag(app):
    """Test recommendation flag"""
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
        
        # Create recommendation comment
        comment = Comment(
            page_id=page.id,
            user_id=user_id,
            content='This should be updated',
            is_recommendation=True
        )
        db.session.add(comment)
        db.session.commit()
        
        assert comment.is_recommendation == True

