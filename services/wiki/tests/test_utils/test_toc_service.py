"""Test TOC service"""

from app.utils.toc_service import generate_toc


def test_toc_generation_basic():
    """Test basic TOC generation"""
    content = """# H1 (not included)
## Section One
### Subsection
## Section Two
"""
    toc = generate_toc(content)
    assert len(toc) == 3
    assert toc[0]["level"] == 2
    assert toc[0]["text"] == "Section One"
    assert toc[1]["level"] == 3
    assert toc[1]["text"] == "Subsection"


def test_toc_anchor_generation():
    """Test anchor generation from headings"""
    content = "## My Heading Here"
    toc = generate_toc(content)
    assert len(toc) == 1
    assert toc[0]["anchor"] == "my-heading-here"


def test_toc_anchor_starts_with_number():
    """Test anchor generation for headings starting with numbers (CSS IDs cannot start with digits)"""
    content = "## 1. Goals & Design Principles"
    toc = generate_toc(content)
    assert len(toc) == 1
    # Should be prefixed with "h-" to make it a valid CSS ID
    assert toc[0]["anchor"] == "h-1-goals-design-principles"
    assert not toc[0]["anchor"][0].isdigit()  # Should not start with a number


def test_toc_excludes_h1():
    """Test that H1 headings are excluded"""
    content = """# Main Title
## Section One
## Section Two
"""
    toc = generate_toc(content)
    assert len(toc) == 2
    assert all(entry["level"] >= 2 for entry in toc)


def test_toc_includes_h2_to_h6():
    """Test that H2-H6 are included"""
    content = """## H2
### H3
#### H4
##### H5
###### H6
"""
    toc = generate_toc(content)
    assert len(toc) == 5
    assert toc[0]["level"] == 2
    assert toc[4]["level"] == 6


def test_toc_with_frontmatter():
    """Test TOC generation with YAML frontmatter"""
    content = """---
title: Test
---
## Section One
## Section Two
"""
    toc = generate_toc(content)
    assert len(toc) == 2
