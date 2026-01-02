"""Tests for Feature 5.3: Three-Way Merge Capabilities"""

from app.sync.merge_utility import MergeUtility


def test_merge_identical_content_no_conflicts():
    """Test merging identical file and database content (no conflicts)"""
    file_content = """# Title

Content line 1
Content line 2
Content line 3
"""
    db_content = """# Title

Content line 1
Content line 2
Content line 3
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is False
    assert conflict_count == 0
    assert merged == file_content  # Should match either (they're identical)


def test_merge_file_additions_no_conflicts():
    """Test merging when file has additions (no conflicts)"""
    file_content = """# Title

Content line 1
Content line 2
New line in file
Content line 3
"""
    db_content = """# Title

Content line 1
Content line 2
Content line 3
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    # Should detect conflict (file has additions that DB doesn't)
    assert has_conflicts is True
    assert conflict_count >= 1
    assert "<<<<<<< FILE" in merged
    assert "=======" in merged
    assert ">>>>>>> DATABASE" in merged
    assert "New line in file" in merged


def test_merge_database_additions_no_conflicts():
    """Test merging when database has additions (no conflicts)"""
    file_content = """# Title

Content line 1
Content line 2
Content line 3
"""
    db_content = """# Title

Content line 1
Content line 2
New line in database
Content line 3
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    # Should detect conflict (DB has additions that file doesn't)
    assert has_conflicts is True
    assert conflict_count >= 1
    assert "<<<<<<< FILE" in merged
    assert "=======" in merged
    assert ">>>>>>> DATABASE" in merged
    assert "New line in database" in merged


def test_merge_conflicting_changes():
    """Test merging when both file and database have conflicting changes"""
    file_content = """# Title

Content line 1
File modified line
Content line 3
"""
    db_content = """# Title

Content line 1
Database modified line
Content line 3
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    assert conflict_count >= 1
    assert "<<<<<<< FILE" in merged
    assert "=======" in merged
    assert ">>>>>>> DATABASE" in merged
    assert "File modified line" in merged
    assert "Database modified line" in merged


def test_merge_common_sequences_preserved():
    """Test that common sequences are preserved in merge"""
    file_content = """# Title

Common line 1
Common line 2
File addition
Common line 3
Common line 4
"""
    db_content = """# Title

Common line 1
Common line 2
Database addition
Common line 3
Common line 4
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    # Common lines should be preserved
    assert "Common line 1" in merged
    assert "Common line 2" in merged
    assert "Common line 3" in merged
    assert "Common line 4" in merged


def test_merge_conflict_markers_format():
    """Test that conflict markers are in correct format"""
    file_content = "File content\nLine 1\nLine 2"
    db_content = "Database content\nLine A\nLine B"

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    assert "<<<<<<< FILE" in merged
    assert "=======" in merged
    assert ">>>>>>> DATABASE" in merged

    # Check marker order
    start_idx = merged.find("<<<<<<< FILE")
    sep_idx = merged.find("=======")
    end_idx = merged.find(">>>>>>> DATABASE")

    assert start_idx < sep_idx < end_idx


def test_merge_empty_files():
    """Test merging empty files"""
    file_content = ""
    db_content = ""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is False
    assert conflict_count == 0
    assert merged == ""


def test_merge_one_empty():
    """Test merging when one source is empty"""
    file_content = "# File content\nLine 1"
    db_content = ""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    assert conflict_count >= 1
    assert "<<<<<<< FILE" in merged
    assert "=======" in merged
    assert ">>>>>>> DATABASE" in merged


def test_merge_multiple_conflicts():
    """Test merging with multiple conflict regions"""
    file_content = """# Title

Line 1
File change 1
Line 3
Line 4
File change 2
Line 6
"""
    db_content = """# Title

Line 1
Database change 1
Line 3
Line 4
Database change 2
Line 6
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    assert conflict_count >= 1  # Should detect at least one conflict
    # Should have conflict markers
    assert merged.count("<<<<<<< FILE") == conflict_count
    assert merged.count("=======") == conflict_count
    assert merged.count(">>>>>>> DATABASE") == conflict_count


def test_merge_frontmatter_preservation():
    """Test that frontmatter is handled correctly in merge"""
    file_content = """---
title: File Title
slug: file-slug
---
# Content

File content line
"""
    db_content = """---
title: Database Title
slug: database-slug
---
# Content

Database content line
"""

    merged, has_conflicts, conflict_count = MergeUtility.merge(file_content, db_content)

    assert has_conflicts is True
    # Both frontmatter versions should be in conflict markers
    assert "File Title" in merged or "Database Title" in merged
    assert "<<<<<<< FILE" in merged
    assert ">>>>>>> DATABASE" in merged
