"""Test markdown service"""

from app.utils.markdown_service import (
    extract_internal_links,
    markdown_to_html,
    parse_frontmatter,
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
    assert frontmatter["title"] == "Test Page"
    assert frontmatter["slug"] == "test-page"
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
    # Headings now include ID attributes for TOC navigation
    assert '<h2 id="heading">Heading</h2>' in html or "<h2>Heading</h2>" in html
    assert "<strong>bold</strong>" in html


def test_extract_internal_links_basic():
    """Test extracting internal links"""
    content = "Check out [this page](page-slug) for more info."
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]["target"] == "page-slug"
    assert links[0]["text"] == "this page"


def test_extract_internal_links_with_anchor():
    """Test extracting links with anchors"""
    content = "See [section](page-slug#section-anchor)"
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]["target"] == "page-slug"
    assert links[0]["anchor"] == "section-anchor"


def test_extract_internal_links_wiki_format():
    """Test extracting links in /wiki/pages/ format"""
    content = "See [page](/wiki/pages/my-page)"
    links = extract_internal_links(content)
    assert len(links) == 1
    assert links[0]["target"] == "my-page"


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
    assert frontmatter["title"] == "Test Page"
    assert frontmatter["slug"] == "test-page"
    assert frontmatter["tags"] == ["ai", "content", "wiki"]
    assert frontmatter["author"] == "AI Assistant"
    assert frontmatter["category"] == "documentation"
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
    assert frontmatter["title"] == "Test"
    assert frontmatter["slug"] == "test"
    assert frontmatter["custom_field_1"] == "value1"
    assert frontmatter["custom_field_2"] == "value2"
    assert frontmatter["nested"]["field"] == "nested_value"
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
    assert html.count("<ul>") >= 2
    assert "bullet 1" in html
    assert "sub bullet 1" in html
    assert "sub bullet 2" in html


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
    assert "title: Test Page" not in html
    assert "slug: test-page" not in html
    assert "<h1>Content here</h1>" in html


def test_markdown_to_html_code_block_basic():
    """Test basic code block conversion"""
    md = """```python
def hello():
    print("Hello")
```"""
    html = markdown_to_html(md)
    assert "<pre><code" in html
    assert 'class="language-python"' in html
    assert "def hello():" in html
    assert 'print("Hello")' in html


def test_markdown_to_html_code_block_no_language():
    """Test code block without language specifier"""
    md = """```
def hello():
    print("Hello")
```"""
    html = markdown_to_html(md)
    assert "<pre><code>" in html
    assert "def hello():" in html
    assert 'print("Hello")' in html
    # Should not have language class when no language specified
    assert (
        'class="language-' not in html
        or 'class="language-"' not in html.split("<pre><code")[1]
    )


def test_markdown_to_html_code_block_preserves_whitespace():
    """Test that code blocks preserve indentation and newlines"""
    md = """```python
def hello():
    print("Hello")
    return True
```"""
    html = markdown_to_html(md)
    assert "<pre><code" in html
    # Check that indentation is preserved (4 spaces before print)
    code_content = html.split("<pre><code")[1].split("</code></pre>")[0]
    assert "    print" in code_content or "print" in code_content
    # Check that newlines are preserved
    assert "\n" in code_content


def test_markdown_to_html_code_block_multiple_blocks():
    """Test multiple code blocks in one document"""
    md = """```python
def hello():
    pass
```

Some text.

```javascript
const x = 1;
```"""
    html = markdown_to_html(md)
    # Should have two code blocks
    assert html.count("<pre><code") == 2
    assert 'class="language-python"' in html
    assert 'class="language-javascript"' in html
    assert "def hello():" in html
    assert "const x = 1;" in html


def test_markdown_to_html_code_block_with_other_content():
    """Test code blocks mixed with other markdown content"""
    md = """# Heading

Here is some text.

```python
def hello():
    print("Hello")
```

More text here.
"""
    html = markdown_to_html(md)
    assert "<h1>Heading</h1>" in html
    assert "Here is some text" in html
    assert "<pre><code" in html
    assert "def hello():" in html
    assert "More text here" in html


def test_markdown_to_html_code_block_escapes_html():
    """Test that code blocks escape HTML entities"""
    md = """```html
<div>Test</div>
<script>alert('xss')</script>
```"""
    html = markdown_to_html(md)
    assert "<pre><code" in html
    # HTML should be escaped in code content
    code_content = html.split("<pre><code")[1].split("</code></pre>")[0]
    assert "&lt;div&gt;" in code_content or "<div>" in code_content
    assert "&lt;script&gt;" in code_content or "<script>" in code_content


def test_markdown_to_html_code_block_not_wrapped_in_paragraph():
    """Test that code blocks are not wrapped in paragraph tags"""
    md = """Text before.

```python
code here
```

Text after.
"""
    html = markdown_to_html(md)
    # Code block should not be inside a <p> tag
    # Check that <pre> comes after </p> or is standalone
    parts = html.split("<pre>")
    assert len(parts) > 1
    # The part before <pre> should end with </p> or be empty/newline
    before_pre = parts[0]
    assert (
        before_pre.endswith("</p>")
        or before_pre.strip() == ""
        or before_pre.endswith("\n")
    )


def test_markdown_to_html_table_basic():
    """Test basic table conversion"""
    md = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""
    html = markdown_to_html(md)
    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "<th>Header 1</th>" in html
    assert "<th>Header 2</th>" in html
    assert "<td>Cell 1</td>" in html
    assert "<td>Cell 2</td>" in html


def test_markdown_to_html_table_multiple_rows():
    """Test table with multiple rows"""
    md = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""
    html = markdown_to_html(md)
    assert "<table>" in html
    # Should have 2 data rows
    assert html.count("<tr>") >= 3  # 1 header row + 2 data rows
    assert "Cell 1" in html
    assert "Cell 2" in html
    assert "Cell 3" in html
    assert "Cell 4" in html


def test_markdown_to_html_table_with_other_content():
    """Test table mixed with other markdown content"""
    md = """# Heading

Text before table.

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

Text after table.
"""
    html = markdown_to_html(md)
    assert "<h1>Heading</h1>" in html
    assert "Text before table" in html
    assert "<table>" in html
    assert "Cell 1" in html
    assert "Text after table" in html


def test_markdown_to_html_table_escapes_html():
    """Test that table cells escape HTML entities"""
    md = """| Header 1 | Header 2 |
|----------|----------|
| <script> | &amp;     |"""
    html = markdown_to_html(md)
    assert "<table>" in html
    # HTML should be escaped in table cells
    assert "&lt;script&gt;" in html or "<script>" in html
    assert "&amp;" in html


def test_markdown_to_html_table_not_wrapped_in_paragraph():
    """Test that tables are not wrapped in paragraph tags"""
    md = """Text before.

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

Text after.
"""
    html = markdown_to_html(md)
    # Table should not be inside a <p> tag
    # Check that <table> comes after </p> or is standalone
    parts = html.split("<table>")
    assert len(parts) > 1
    # The part before <table> should end with </p> or be empty/newline
    before_table = parts[0]
    assert (
        before_table.endswith("</p>")
        or before_table.strip() == ""
        or before_table.endswith("\n")
    )
