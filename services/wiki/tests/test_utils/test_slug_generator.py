"""Test slug generator"""
from app.utils.slug_generator import generate_slug, validate_slug


def test_generate_slug_basic():
    """Test basic slug generation"""
    slug = generate_slug("Hello World")
    assert slug == "hello-world"


def test_generate_slug_special_chars():
    """Test slug generation with special characters"""
    slug = generate_slug("Test & Example!")
    assert slug == "test-example"


def test_generate_slug_unicode():
    """Test slug generation with unicode characters"""
    slug = generate_slug("Café & Résumé")
    assert slug == "cafe-resume"


def test_generate_slug_uniqueness():
    """Test slug uniqueness enforcement"""
    existing = ["test", "test-1", "test-2"]
    slug = generate_slug("Test", existing_slugs=existing)
    assert slug == "test-3"


def test_generate_slug_empty_text():
    """Test that empty text raises error"""
    import pytest
    with pytest.raises(ValueError):
        generate_slug("")


def test_validate_slug_valid():
    """Test validation of valid slugs"""
    assert validate_slug("hello-world") == True
    assert validate_slug("test_123") == True
    assert validate_slug("a") == True


def test_validate_slug_invalid():
    """Test validation of invalid slugs"""
    assert validate_slug("") == False
    assert validate_slug("-invalid") == False
    assert validate_slug("invalid-") == False
    assert validate_slug("invalid slug") == False
    assert validate_slug("Invalid!") == False

