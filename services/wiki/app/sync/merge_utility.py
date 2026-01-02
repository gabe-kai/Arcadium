"""
Merge utility for merging conflicting file and database content.

Handles automatic merging of conflicting edits and marks conflicts for manual resolution.
Uses a two-way merge strategy: compares file and database versions, merges non-conflicting
changes, and marks conflicts with Git-style conflict markers.
"""

import difflib
from typing import Tuple


class MergeUtility:
    """Utility for merging conflicting content versions"""

    CONFLICT_START_MARKER = "<<<<<<< FILE\n"
    CONFLICT_SEPARATOR = "=======\n"
    CONFLICT_END_MARKER = ">>>>>>> DATABASE\n"

    @staticmethod
    def merge(file_content: str, db_content: str) -> Tuple[str, bool, int]:
        """
        Merge file and database content, marking conflicts where they differ.

        Uses a two-way merge strategy: finds common sequences between file and database
        versions, merges non-conflicting changes, and marks conflicts with Git-style
        conflict markers.

        Args:
            file_content: File version content
            db_content: Database version content

        Returns:
            Tuple of (merged_content, has_conflicts, conflict_count)
            - merged_content: Merged content with conflict markers if conflicts exist
            - has_conflicts: True if conflicts were detected
            - conflict_count: Number of conflicts found
        """
        file_lines = file_content.splitlines(keepends=True)
        db_lines = db_content.splitlines(keepends=True)

        merged_lines = []
        has_conflicts = False
        conflict_count = 0

        # Use SequenceMatcher to find common sequences
        matcher = difflib.SequenceMatcher(None, file_lines, db_lines)
        matching_blocks = matcher.get_matching_blocks()

        file_pos = 0
        db_pos = 0

        for match in matching_blocks:
            # Get changes before this match
            file_changes = file_lines[file_pos : match.a]
            db_changes = db_lines[db_pos : match.b]

            if file_changes or db_changes:
                if file_changes != db_changes:
                    # Changes differ - conflict
                    has_conflicts = True
                    conflict_count += 1
                    merged_lines.append(MergeUtility.CONFLICT_START_MARKER)
                    merged_lines.extend(file_changes)
                    merged_lines.append(MergeUtility.CONFLICT_SEPARATOR)
                    merged_lines.extend(db_changes)
                    merged_lines.append(MergeUtility.CONFLICT_END_MARKER)
                else:
                    # Same changes - use either
                    merged_lines.extend(file_changes)

            # Add matching block (unchanged content)
            merged_lines.extend(file_lines[match.a : match.a + match.size])

            file_pos = match.a + match.size
            db_pos = match.b + match.size

        # Handle remaining content at the end
        if file_pos < len(file_lines) or db_pos < len(db_lines):
            file_remaining = file_lines[file_pos:]
            db_remaining = db_lines[db_pos:]

            if file_remaining != db_remaining:
                has_conflicts = True
                conflict_count += 1
                merged_lines.append(MergeUtility.CONFLICT_START_MARKER)
                merged_lines.extend(file_remaining)
                merged_lines.append(MergeUtility.CONFLICT_SEPARATOR)
                merged_lines.extend(db_remaining)
                merged_lines.append(MergeUtility.CONFLICT_END_MARKER)
            else:
                merged_lines.extend(file_remaining)

        merged_content = "".join(merged_lines)

        return merged_content, has_conflicts, conflict_count
