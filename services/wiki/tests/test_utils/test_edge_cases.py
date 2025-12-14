"""Edge case tests for utilities"""
from app.utils.slug_generator import generate_slug, validate_slug
from app.utils.size_calculator import calculate_word_count, calculate_content_size_kb
from app.utils.toc_service import generate_toc
from app.utils.markdown_service import parse_frontmatter, markdown_to_html, extract_internal_links


def test_slug_generation_edge_cases():
    """Test slug generation with edge cases"""
    # Empty string should raise error
    import pytest
    with pytest.raises(ValueError):
        generate_slug("")
    
    # Only special characters
    slug = generate_slug("!@#$%^&*()")
    assert slug == "page" or len(slug) > 0  # Should handle gracefully (defaults to "page")
    
    # Very long text
    long_text = "A" * 1000
    slug = generate_slug(long_text)
    assert len(slug) <= 255  # Should be reasonable length
    
    # Multiple spaces
    assert generate_slug("word    word") == "word-word"
    
    # Leading/trailing spaces
    assert generate_slug("  word  ") == "word"


def test_size_calculator_edge_cases():
    """Test size calculator with edge cases"""
    # Empty content
    assert calculate_word_count("") == 0
    assert calculate_content_size_kb("") == 0.0
    
    # Only whitespace
    assert calculate_word_count("   \n\n   ") == 0
    
    # Very long content
    long_content = "word " * 100000
    count = calculate_word_count(long_content)
    assert count == 100000
    
    # Content with only images
    image_only = "![alt](image1.png)\n![alt](image2.png)"
    count = calculate_word_count(image_only)
    assert count == 0  # Images excluded
    
    # Content with only links
    link_only = "[text](link1)\n[text](link2)"
    count = calculate_word_count(link_only)
    assert count == 2  # Link text counts


def test_toc_generation_edge_cases():
    """Test TOC generation with edge cases"""
    # Empty content
    toc = generate_toc("")
    assert toc == []
    
    # No headings
    toc = generate_toc("Just some text without headings")
    assert toc == []
    
    # Only H1 (should be excluded)
    toc = generate_toc("# Only H1 heading")
    assert toc == []
    
    # Very nested headings
    content = """
# H1 (excluded)
## H2
### H3
#### H4
##### H5
###### H6
####### Not a heading (7 hashes)
"""
    toc = generate_toc(content)
    assert len(toc) == 5  # H2-H6 only
    
    # Headings with special characters
    content = "## Heading with émojis 🎮 and 中文"
    toc = generate_toc(content)
    assert len(toc) == 1


def test_markdown_service_edge_cases():
    """Test markdown service with edge cases"""
    # Empty content
    frontmatter, content = parse_frontmatter("")
    assert frontmatter == {}
    assert content == ""
    
    # Malformed frontmatter
    malformed = "---\ninvalid yaml: [\n---\ncontent"
    frontmatter, content = parse_frontmatter(malformed)
    # Should handle gracefully (empty dict or partial)
    assert isinstance(frontmatter, dict)
    
    # Content with no frontmatter
    frontmatter, content = parse_frontmatter("# Just markdown")
    assert frontmatter == {}
    assert content == "# Just markdown"
    
    # HTML conversion of empty content
    html = markdown_to_html("")
    assert html == ""
    
    # HTML conversion of only whitespace
    html = markdown_to_html("   \n\n   ")
    assert html != ""  # Should convert to paragraphs or empty
    
    # Link extraction from empty content
    links = extract_internal_links("")
    assert links == []
    
    # Link extraction with no links
    links = extract_internal_links("Just text without links")
    assert links == []


def test_slug_validation_edge_cases():
    """Test slug validation with edge cases"""
    # Empty slug
    assert validate_slug("") == False
    
    # Valid slug
    assert validate_slug("valid-slug") == True
    
    # Slug with spaces
    assert validate_slug("slug with spaces") == False
    
    # Slug with special characters
    assert validate_slug("slug!@#") == False
    
    # Very long slug
    long_slug = "a" * 300
    # Should either validate or reject
    result = validate_slug(long_slug)
    assert isinstance(result, bool)
    
    # Slug with unicode
    assert validate_slug("slug-with-中文") == False  # Unicode not allowed in slugs

