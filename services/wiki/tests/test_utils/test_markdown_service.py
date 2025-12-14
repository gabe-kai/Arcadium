"""Test markdown service"""
from app.utils.markdown_service import (
    parse_frontmatter,
    markdown_to_html,
    extract_internal_links
)


def test_parse_frontmatter_with_frontmatter():
    """Test parsing content with frontmatter"""
    content = """---
title: Test Page
slug: test-page
---
# Content here
"""
    frontmatter, markdown = parse_frontmatter(content)
    assert frontmatter['title'] == "Test Page"
    assert frontmatter['slug'] == "test-page"
    assert "# Content here" in markdown


def test_parse_frontmatter_without_frontmatter():
    """Test parsing content without frontmatter"""
    content = "# Just markdown content"
    frontmatter, markdown = parse_frontmatter(content)
    assert frontmatter == {}
    assert markdown == content


def test_markdown_to_html_basic():
    """Test basic markdown to HTML conversion"""
    md = "## Heading\n\nThis is **bold** text."
    html = markdown_to_html(md)
    assert "<h2>Heading</h2>" in html
    assert "<strong>bold</strong>" in html


def test_extract_internal_links_basic():
    """Test extracting internal links"""
    content = "Check out [this page](page-slug) for more info."
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]['target'] == "page-slug"
    assert links[0]['text'] == "this page"


def test_extract_internal_links_with_anchor():
    """Test extracting links with anchors"""
    content = "See [section](page-slug#section-anchor)"
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]['target'] == "page-slug"
    assert links[0]['anchor'] == "section-anchor"


def test_extract_internal_links_wiki_format():
    """Test extracting links in /wiki/pages/ format"""
    content = "See [page](/wiki/pages/my-page)"
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]['target'] == "my-page"

