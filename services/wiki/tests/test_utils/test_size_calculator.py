"""Test size calculator"""
from app.utils.size_calculator import calculate_word_count, calculate_content_size_kb


def test_word_count_basic():
    """Test basic word count"""
    content = "This is a test"
    assert calculate_word_count(content) == 4


def test_word_count_excludes_images():
    """Test that images are excluded from word count"""
    content = "This is a test. ![Image](url.png) More words here."
    # After removing image: "This is a test. More words here." = 7 words
    assert calculate_word_count(content) == 7


def test_word_count_excludes_links_but_keeps_text():
    """Test that link syntax is removed but text is kept"""
    content = "Check out [this link](url) for more info."
    # Should count: "Check out this link for more info" = 7 words
    assert calculate_word_count(content) == 7


def test_word_count_with_frontmatter():
    """Test that frontmatter is excluded"""
    content = """---
title: Test
---
This is the actual content.
"""
    # Should count: "This is the actual content" = 5 words
    assert calculate_word_count(content) == 5


def test_content_size_kb():
    """Test content size calculation"""
    content = "x" * 1024  # 1KB of content
    size = calculate_content_size_kb(content)
    assert size == 1.0


def test_content_size_excludes_images():
    """Test that images don't count toward size"""
    # Create content with images (image syntax should be removed)
    content_with_image = "Text " + "![Image](url.png) " * 10
    # Create equivalent content without images (just the text)
    content_without = "Text " * 10
    
    # Sizes should be similar since image syntax is removed
    size_with = calculate_content_size_kb(content_with_image)
    size_without = calculate_content_size_kb(content_without)
    
    # Image syntax removal means sizes should be very close
    # Allow for some variance due to whitespace differences
    assert abs(size_with - size_without) < 0.1  # Within 0.1 KB

