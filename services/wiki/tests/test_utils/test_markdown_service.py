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


def test_parse_frontmatter_with_custom_fields():
    """Test parsing frontmatter with custom fields (e.g., from AI system)"""
    content = """---
title: Test Page
slug: test-page
tags: [ai, content, wiki]
author: AI Assistant
category: documentation
---
# Content here
"""
    frontmatter, markdown = parse_frontmatter(content)
    assert frontmatter['title'] == "Test Page"
    assert frontmatter['slug'] == "test-page"
    assert frontmatter['tags'] == ['ai', 'content', 'wiki']
    assert frontmatter['author'] == "AI Assistant"
    assert frontmatter['category'] == "documentation"
    assert "# Content here" in markdown


def test_parse_frontmatter_preserves_all_fields():
    """Test that parse_frontmatter preserves all YAML fields"""
    content = """---
title: Test
slug: test
custom_field_1: value1
custom_field_2: value2
nested:
  field: nested_value
---
Content
"""
    frontmatter, markdown = parse_frontmatter(content)
    assert frontmatter['title'] == "Test"
    assert frontmatter['slug'] == "test"
    assert frontmatter['custom_field_1'] == "value1"
    assert frontmatter['custom_field_2'] == "value2"
    assert frontmatter['nested']['field'] == "nested_value"
    assert "Content" in markdown


def test_markdown_to_html_with_nested_lists():
    """Test markdown to HTML conversion with nested lists"""
    md = """- bullet 1
- bullet 2
    - sub bullet 1
        - sub bullet 2
"""
    html = markdown_to_html(md)
    # Should have nested ul tags
    assert html.count('<ul>') >= 2
    assert 'bullet 1' in html
    assert 'sub bullet 1' in html
    assert 'sub bullet 2' in html


def test_markdown_to_html_excludes_frontmatter():
    """Test that markdown_to_html doesn't include frontmatter in output"""
    content = """---
title: Test Page
slug: test-page
---
# Content here
"""
    frontmatter, markdown = parse_frontmatter(content)
    html = markdown_to_html(markdown)
    # HTML should not contain frontmatter fields
    assert 'title: Test Page' not in html
    assert 'slug: test-page' not in html
    assert '<h1>Content here</h1>' in html

