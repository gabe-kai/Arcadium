"""Table of Contents generation from markdown headings"""

import re
from typing import Dict, List


def generate_toc(content: str) -> List[Dict[str, str]]:
    """
    Generate table of contents from markdown headings (H2-H6).

    Args:
        content: Markdown content string

    Returns:
        List of TOC entries with 'level', 'text', and 'anchor'
    """
    toc = []
    if not content:
        return toc

    # Remove YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].lstrip("\n")

    # Pattern to match markdown headings (H2-H6)
    # Matches: ## Heading, ### Heading, etc.
    heading_pattern = re.compile(r"^(#{2,6})\s+(.+)$", re.MULTILINE)

    for match in heading_pattern.finditer(content):
        level = len(match.group(1))  # Number of # characters (2-6)
        text = match.group(2).strip()

        # Generate anchor from heading text
        anchor = _generate_anchor(text)

        toc.append({"level": level, "text": text, "anchor": anchor})

    return toc


def _generate_anchor(text: str) -> str:
    """
    Generate an anchor ID from heading text.
    Converts to lowercase, replaces spaces with hyphens, removes special chars.

    Args:
        text: Heading text

    Returns:
        Anchor string (e.g., "my-heading")
    """
    # Convert to lowercase
    anchor = text.lower()

    # Replace spaces and special chars with hyphens
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"[-\s]+", "-", anchor)

    # Remove leading/trailing hyphens
    anchor = anchor.strip("-")

    return anchor or "heading"
