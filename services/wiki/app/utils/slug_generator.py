"""Slug generation and validation utilities"""
import re
import unicodedata
from typing import Optional


def generate_slug(text: str, existing_slugs: Optional[list] = None) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: The text to convert to a slug
        existing_slugs: List of existing slugs to check for uniqueness
        
    Returns:
        A unique slug
    """
    if not text:
        raise ValueError("Text cannot be empty")
    
    # Convert to lowercase
    slug = text.lower()
    
    # Remove accents and special characters
    slug = unicodedata.normalize('NFKD', slug)
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure it's not empty
    if not slug:
        slug = 'page'
    
    # Ensure uniqueness
    if existing_slugs:
        base_slug = slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    return slug


def validate_slug(slug: str) -> bool:
    """
    Validate that a slug is in the correct format.
    
    Args:
        slug: The slug to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not slug:
        return False
    
    # Check length (reasonable limits)
    if len(slug) < 1 or len(slug) > 255:
        return False
    
    # Check format: alphanumeric, hyphens, underscores only
    if not re.match(r'^[a-z0-9_-]+$', slug):
        return False
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False
    
    return True

