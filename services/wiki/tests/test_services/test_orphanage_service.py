"""Test orphanage service"""
import os
import uuid
import tempfile
import shutil
from app.services.orphanage_service import OrphanageService
from app.services.page_service import PageService
from app.models.page import Page
from app import db


def test_get_or_create_orphanage(app):
    """Test getting or creating orphanage"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # First call should create it
        orphanage1 = OrphanageService.get_or_create_orphanage(user_id)
        assert orphanage1.slug == "orphanage"
        assert orphanage1.is_system_page == True
        
        # Second call should return the same one
        orphanage2 = OrphanageService.get_or_create_orphanage(user_id)
        assert orphanage1.id == orphanage2.id


def test_orphan_pages(app):
    """Test orphaning pages"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
            user_id = uuid.uuid4()
            
            # Create parent and children
            parent = PageService.create_page(
                title="Parent",
                content="Parent content",
                user_id=user_id
            )
            
            child1 = PageService.create_page(
                title="Child 1",
                content="Child 1 content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            child2 = PageService.create_page(
                title="Child 2",
                content="Child 2 content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            # Orphan the children
            orphaned = OrphanageService.orphan_pages(
                [child1.id, child2.id],
                parent.id
            )
            
            assert len(orphaned) == 2
            
            # Check they're marked as orphaned
            child1 = Page.query.get(child1.id)
            child2 = Page.query.get(child2.id)
            
            assert child1.is_orphaned == True
            assert child1.orphaned_from == parent.id
            assert child2.is_orphaned == True
            assert child2.orphaned_from == parent.id
            
            # Check they're under orphanage
            orphanage = OrphanageService.get_or_create_orphanage(user_id)
            assert child1.parent_id == orphanage.id
            assert child2.parent_id == orphanage.id
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_get_orphaned_pages(app):
    """Test getting orphaned pages"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
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
            
            child1 = PageService.create_page(
                title="Child 1",
                content="Content",
                user_id=user_id,
                parent_id=parent1.id
            )
            
            child2 = PageService.create_page(
                title="Child 2",
                content="Content",
                user_id=user_id,
                parent_id=parent1.id
            )
            
            child3 = PageService.create_page(
                title="Child 3",
                content="Content",
                user_id=user_id,
                parent_id=parent2.id
            )
            
            # Orphan children
            OrphanageService.orphan_pages([child1.id, child2.id], parent1.id)
            OrphanageService.orphan_pages([child3.id], parent2.id)
            
            # Get all orphaned
            orphaned = OrphanageService.get_orphaned_pages()
            assert len(orphaned) == 3
            
            # Get grouped
            grouped = OrphanageService.get_orphaned_pages(grouped=True)
            assert len(grouped) == 2  # Two parent groups
            assert str(parent1.id) in grouped
            assert str(parent2.id) in grouped
            assert len(grouped[str(parent1.id)]) == 2
            assert len(grouped[str(parent2.id)]) == 1
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_reassign_page(app):
    """Test reassigning an orphaned page"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
            user_id = uuid.uuid4()
            
            # Create structure
            old_parent = PageService.create_page(
                title="Old Parent",
                content="Content",
                user_id=user_id
            )
            
            new_parent = PageService.create_page(
                title="New Parent",
                content="Content",
                user_id=user_id
            )
            
            child = PageService.create_page(
                title="Child",
                content="Content",
                user_id=user_id,
                parent_id=old_parent.id
            )
            
            # Orphan child
            OrphanageService.orphan_pages([child.id], old_parent.id)
            
            # Reassign to new parent
            reassigned = OrphanageService.reassign_page(
                child.id,
                new_parent.id,
                user_id
            )
            
            assert reassigned.is_orphaned == False
            assert reassigned.parent_id == new_parent.id
            assert reassigned.orphaned_from is None
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_reassign_page_to_root(app):
    """Test reassigning an orphaned page to root"""
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
            
            child = PageService.create_page(
                title="Child",
                content="Content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            # Orphan child
            OrphanageService.orphan_pages([child.id], parent.id)
            
            # Reassign to root
            reassigned = OrphanageService.reassign_page(
                child.id,
                None,
                user_id
            )
            
            assert reassigned.is_orphaned == False
            assert reassigned.parent_id is None
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_bulk_reassign_pages(app):
    """Test bulk reassigning orphaned pages"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
            user_id = uuid.uuid4()
            
            old_parent = PageService.create_page(
                title="Old Parent",
                content="Content",
                user_id=user_id
            )
            
            new_parent = PageService.create_page(
                title="New Parent",
                content="Content",
                user_id=user_id
            )
            
            child1 = PageService.create_page(
                title="Child 1",
                content="Content",
                user_id=user_id,
                parent_id=old_parent.id
            )
            
            child2 = PageService.create_page(
                title="Child 2",
                content="Content",
                user_id=user_id,
                parent_id=old_parent.id
            )
            
            # Orphan children
            OrphanageService.orphan_pages([child1.id, child2.id], old_parent.id)
            
            # Bulk reassign
            reassigned = OrphanageService.bulk_reassign_pages(
                [child1.id, child2.id],
                new_parent.id,
                user_id
            )
            
            assert len(reassigned) == 2
            assert all(not p.is_orphaned for p in reassigned)
            assert all(p.parent_id == new_parent.id for p in reassigned)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_clear_orphanage(app):
    """Test clearing the orphanage"""
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
            
            # Orphan children
            OrphanageService.orphan_pages([child1.id, child2.id], parent.id)
            
            # Clear orphanage
            result = OrphanageService.clear_orphanage(user_id)
            
            assert result['reassigned_count'] == 2
            
            # Check pages are no longer orphaned
            child1 = Page.query.get(child1.id)
            child2 = Page.query.get(child2.id)
            
            assert child1.is_orphaned == False
            assert child1.parent_id is None
            assert child2.is_orphaned == False
            assert child2.parent_id is None
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_get_orphanage_stats(app):
    """Test getting orphanage statistics"""
    with app.app_context():
        temp_dir = tempfile.mkdtemp()
        app.config['WIKI_PAGES_DIR'] = temp_dir
        
        try:
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
            
            child1 = PageService.create_page(
                title="Child 1",
                content="Content",
                user_id=user_id,
                parent_id=parent1.id
            )
            
            child2 = PageService.create_page(
                title="Child 2",
                content="Content",
                user_id=user_id,
                parent_id=parent1.id
            )
            
            child3 = PageService.create_page(
                title="Child 3",
                content="Content",
                user_id=user_id,
                parent_id=parent2.id
            )
            
            # Orphan children
            OrphanageService.orphan_pages([child1.id, child2.id], parent1.id)
            OrphanageService.orphan_pages([child3.id], parent2.id)
            
            # Get stats
            stats = OrphanageService.get_orphanage_stats()
            
            assert stats['total_orphaned'] == 3
            assert stats['groups'] == 2
            assert str(parent1.id) in stats['by_parent']
            assert str(parent2.id) in stats['by_parent']
            assert stats['by_parent'][str(parent1.id)] == 2
            assert stats['by_parent'][str(parent2.id)] == 1
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_reassign_page_circular_reference(app):
    """Test that circular references are prevented during reassignment"""
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
            
            child = PageService.create_page(
                title="Child",
                content="Content",
                user_id=user_id,
                parent_id=parent.id
            )
            
            # Orphan child
            OrphanageService.orphan_pages([child.id], parent.id)
            
            # Try to reassign parent to child (should fail)
            import pytest
            with pytest.raises(ValueError, match="circular"):
                OrphanageService.reassign_page(
                    parent.id,
                    child.id,
                    user_id
                )
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


