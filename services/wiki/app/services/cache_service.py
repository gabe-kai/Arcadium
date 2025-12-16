"""
Caching service for performance optimization.

Provides caching for:
- Rendered HTML content
- Table of Contents (TOC) generation
- Other frequently accessed data
"""
import hashlib
import json
from typing import Optional, Dict, List
from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models.wiki_config import WikiConfig


class CacheService:
    """Service for managing application caches"""
    
    CACHE_PREFIX = "cache_"
    CACHE_TTL_KEY = "cache_ttl_seconds"
    DEFAULT_TTL = 3600  # 1 hour default TTL
    
    @staticmethod
    def _generate_cache_key(content: str, cache_type: str) -> str:
        """
        Generate a cache key from content.
        
        Args:
            content: Content to cache
            cache_type: Type of cache (e.g., 'html', 'toc')
            
        Returns:
            Cache key string
        """
        # Create hash of content
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        return f"{CacheService.CACHE_PREFIX}{cache_type}_{content_hash}"
    
    @staticmethod
    def _get_cache_ttl() -> int:
        """Get cache TTL in seconds from config"""
        config = db.session.query(WikiConfig).filter_by(
            key=CacheService.CACHE_TTL_KEY
        ).first()
        
        if config:
            try:
                return int(config.value)
            except (ValueError, TypeError):
                pass
        
        return CacheService.DEFAULT_TTL
    
    @staticmethod
    def get_html_cache(content: str) -> Optional[str]:
        """
        Get cached HTML for content.
        
        Args:
            content: Markdown content
            
        Returns:
            Cached HTML string or None if not found/expired
        """
        cache_key = CacheService._generate_cache_key(content, 'html')
        config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
        
        if not config:
            return None
        
        # Check if cache is expired
        try:
            cache_data = json.loads(config.value)
            cached_at = datetime.fromisoformat(cache_data.get('cached_at', ''))
            ttl = CacheService._get_cache_ttl()
            
            age_seconds = (datetime.now(timezone.utc) - cached_at.replace(tzinfo=timezone.utc)).total_seconds()
            if age_seconds > ttl:
                # Cache expired, delete it
                db.session.delete(config)
                db.session.commit()
                return None
            
            return cache_data.get('html')
        except (json.JSONDecodeError, ValueError, KeyError):
            # Invalid cache data, delete it
            db.session.delete(config)
            db.session.commit()
            return None
    
    @staticmethod
    def set_html_cache(content: str, html: str, user_id: Optional[str] = None):
        """
        Cache HTML for content.
        
        Args:
            content: Markdown content
            html: Rendered HTML
            user_id: User ID for cache creation (optional)
        """
        cache_key = CacheService._generate_cache_key(content, 'html')
        cache_data = {
            'html': html,
            'cached_at': datetime.now(timezone.utc).isoformat()
        }
        
        config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
        if config:
            config.value = json.dumps(cache_data)
            if user_id:
                config.updated_by = user_id
        else:
            config = WikiConfig(
                key=cache_key,
                value=json.dumps(cache_data),
                updated_by=user_id
            )
            db.session.add(config)
        
        db.session.commit()
    
    @staticmethod
    def get_toc_cache(content: str) -> Optional[List[Dict]]:
        """
        Get cached TOC for content.
        
        Args:
            content: Markdown content
            
        Returns:
            Cached TOC list or None if not found/expired
        """
        cache_key = CacheService._generate_cache_key(content, 'toc')
        config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
        
        if not config:
            return None
        
        # Check if cache is expired
        try:
            cache_data = json.loads(config.value)
            cached_at = datetime.fromisoformat(cache_data.get('cached_at', ''))
            ttl = CacheService._get_cache_ttl()
            
            age_seconds = (datetime.now(timezone.utc) - cached_at.replace(tzinfo=timezone.utc)).total_seconds()
            if age_seconds > ttl:
                # Cache expired, delete it
                db.session.delete(config)
                db.session.commit()
                return None
            
            return cache_data.get('toc')
        except (json.JSONDecodeError, ValueError, KeyError):
            # Invalid cache data, delete it
            db.session.delete(config)
            db.session.commit()
            return None
    
    @staticmethod
    def set_toc_cache(content: str, toc: List[Dict], user_id: Optional[str] = None):
        """
        Cache TOC for content.
        
        Args:
            content: Markdown content
            toc: TOC list
            user_id: User ID for cache creation (optional)
        """
        cache_key = CacheService._generate_cache_key(content, 'toc')
        cache_data = {
            'toc': toc,
            'cached_at': datetime.now(timezone.utc).isoformat()
        }
        
        config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
        if config:
            config.value = json.dumps(cache_data)
            if user_id:
                config.updated_by = user_id
        else:
            config = WikiConfig(
                key=cache_key,
                value=json.dumps(cache_data),
                updated_by=user_id
            )
            db.session.add(config)
        
        db.session.commit()
    
    @staticmethod
    def invalidate_cache(content: str, cache_type: Optional[str] = None):
        """
        Invalidate cache for content.
        
        Args:
            content: Markdown content
            cache_type: Type of cache to invalidate ('html', 'toc', or None for both)
        """
        if cache_type:
            cache_key = CacheService._generate_cache_key(content, cache_type)
            config = db.session.query(WikiConfig).filter_by(key=cache_key).first()
            if config:
                db.session.delete(config)
        else:
            # Invalidate both
            html_key = CacheService._generate_cache_key(content, 'html')
            toc_key = CacheService._generate_cache_key(content, 'toc')
            db.session.query(WikiConfig).filter(
                WikiConfig.key.in_([html_key, toc_key])
            ).delete(synchronize_session=False)
        
        db.session.commit()
    
    @staticmethod
    def clear_all_caches():
        """Clear all cached data"""
        db.session.query(WikiConfig).filter(
            WikiConfig.key.like(f"{CacheService.CACHE_PREFIX}%")
        ).delete(synchronize_session=False)
        db.session.commit()
