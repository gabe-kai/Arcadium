"""Tests for cache service"""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from app import db
from app.models.wiki_config import WikiConfig
from app.services.cache_service import CacheService


@pytest.fixture
def test_user_id():
    """Test user ID fixture"""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_get_html_cache_not_found(app):
    """Test getting HTML cache when not cached"""
    with app.app_context():
        result = CacheService.get_html_cache("test content")
        assert result is None


def test_set_and_get_html_cache(app, test_user_id):
    """Test setting and getting HTML cache"""
    with app.app_context():
        content = "# Test Content\n\nThis is test content."
        html = "<h1>Test Content</h1><p>This is test content.</p>"
        
        CacheService.set_html_cache(content, html, str(test_user_id))
        
        cached = CacheService.get_html_cache(content)
        assert cached == html


def test_get_toc_cache_not_found(app):
    """Test getting TOC cache when not cached"""
    with app.app_context():
        result = CacheService.get_toc_cache("test content")
        assert result is None


def test_set_and_get_toc_cache(app, test_user_id):
    """Test setting and getting TOC cache"""
    with app.app_context():
        content = "# Title\n\n## Section 1\n\n### Subsection"
        toc = [
            {'level': 2, 'text': 'Section 1', 'anchor': 'section-1'},
            {'level': 3, 'text': 'Subsection', 'anchor': 'subsection'}
        ]
        
        CacheService.set_toc_cache(content, toc, str(test_user_id))
        
        cached = CacheService.get_toc_cache(content)
        assert cached == toc


def test_html_cache_expiration(app, test_user_id):
    """Test that HTML cache expires after TTL"""
    with app.app_context():
        content = "test content"
        html = "<p>test content</p>"
        
        # Set cache with old timestamp
        cache_key = CacheService._generate_cache_key(content, 'html')
        old_cache_data = {
            'html': html,
            'cached_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        }
        
        import json
        config = WikiConfig(
            key=cache_key,
            value=json.dumps(old_cache_data),
            updated_by=test_user_id
        )
        db.session.add(config)
        db.session.commit()
        
        # Should return None (expired)
        result = CacheService.get_html_cache(content)
        assert result is None
        
        # Cache should be deleted
        config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
        assert config is None


def test_toc_cache_expiration(app, test_user_id):
    """Test that TOC cache expires after TTL"""
    with app.app_context():
        content = "## Section"
        toc = [{'level': 2, 'text': 'Section', 'anchor': 'section'}]
        
        # Set cache with old timestamp
        cache_key = CacheService._generate_cache_key(content, 'toc')
        old_cache_data = {
            'toc': toc,
            'cached_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        }
        
        import json
        config = WikiConfig(
            key=cache_key,
            value=json.dumps(old_cache_data),
            updated_by=test_user_id
        )
        db.session.add(config)
        db.session.commit()
        
        # Should return None (expired)
        result = CacheService.get_toc_cache(content)
        assert result is None


def test_invalidate_cache_html(app, test_user_id):
    """Test invalidating HTML cache"""
    with app.app_context():
        content = "test content"
        html = "<p>test</p>"
        
        CacheService.set_html_cache(content, html, str(test_user_id))
        CacheService.invalidate_cache(content, 'html')
        
        result = CacheService.get_html_cache(content)
        assert result is None


def test_invalidate_cache_toc(app, test_user_id):
    """Test invalidating TOC cache"""
    with app.app_context():
        content = "## Section"
        toc = [{'level': 2, 'text': 'Section', 'anchor': 'section'}]
        
        CacheService.set_toc_cache(content, toc, str(test_user_id))
        CacheService.invalidate_cache(content, 'toc')
        
        result = CacheService.get_toc_cache(content)
        assert result is None


def test_invalidate_cache_both(app, test_user_id):
    """Test invalidating both HTML and TOC cache"""
    with app.app_context():
        content = "## Section"
        html = "<h2>Section</h2>"
        toc = [{'level': 2, 'text': 'Section', 'anchor': 'section'}]
        
        CacheService.set_html_cache(content, html, str(test_user_id))
        CacheService.set_toc_cache(content, toc, str(test_user_id))
        
        CacheService.invalidate_cache(content)
        
        assert CacheService.get_html_cache(content) is None
        assert CacheService.get_toc_cache(content) is None


def test_cache_key_generation():
    """Test that cache keys are generated consistently"""
    content = "test content"
    key1 = CacheService._generate_cache_key(content, 'html')
    key2 = CacheService._generate_cache_key(content, 'html')
    
    assert key1 == key2
    assert key1.startswith('cache_html_')
    
    # Different content should generate different key
    key3 = CacheService._generate_cache_key("different content", 'html')
    assert key1 != key3
    
    # Different cache type should generate different key
    key4 = CacheService._generate_cache_key(content, 'toc')
    assert key1 != key4


def test_clear_all_caches(app, test_user_id):
    """Test clearing all caches"""
    with app.app_context():
        content1 = "content 1"
        content2 = "content 2"
        
        CacheService.set_html_cache(content1, "<p>1</p>", str(test_user_id))
        CacheService.set_toc_cache(content1, [], str(test_user_id))
        CacheService.set_html_cache(content2, "<p>2</p>", str(test_user_id))
        
        CacheService.clear_all_caches()
        
        assert CacheService.get_html_cache(content1) is None
        assert CacheService.get_toc_cache(content1) is None
        assert CacheService.get_html_cache(content2) is None
