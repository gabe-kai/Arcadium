"""Markdown processing utilities"""

import re
from typing import Dict, Optional, Tuple

import yaml
from app.utils.toc_service import _generate_anchor


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, markdown_content)
    """
    if not content.startswith("---"):
        return {}, content

    # Split on frontmatter delimiters
    parts = content.split("---", 2)

    if len(parts) < 3:
        # Malformed frontmatter, return as-is
        return {}, content

    frontmatter_str = parts[1].strip()
    markdown_content = parts[2].lstrip("\n")

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        # Invalid YAML, return empty dict
        frontmatter = {}

    return frontmatter, markdown_content


def _parse_lists(lines: list) -> list:
    """
    Parse markdown list lines into HTML list structure.
    Handles nested bullet and numbered lists.

    Args:
        lines: List of markdown lines

    Returns:
        List of HTML strings with lists converted
    """
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        original_line = line
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            result.append("")
            i += 1
            continue

        # Skip lines that are already HTML tags (e.g., <hr>, <h2>, etc.)
        # This prevents processing horizontal rules or headings as list items
        if stripped.startswith("<") and stripped.endswith(">"):
            result.append(line)
            i += 1
            continue

        # Skip horizontal rules (---, ***, ___, * * *, - - -, _ _ _) - they should already be converted to <hr>
        # but check here as a safeguard to prevent them from being processed as list items
        if re.match(r"^([-*_])\1{2,}\s*$", stripped) or re.match(
            r"^([-*_])(?:\s+\1){2,}\s*$", stripped
        ):
            result.append(line)
            i += 1
            continue

        # Check if this is a list item (bullet or numbered)
        bullet_match = re.match(r"^(\s*)[-*+]\s+(.+)$", stripped)
        numbered_match = re.match(r"^(\s*)(\d+)\.\s+(.+)$", stripped)

        if bullet_match or numbered_match:
            # Start of a list - collect all list items at this level
            list_items = []
            list_type = "ul" if bullet_match else "ol"
            base_indent = (
                len(bullet_match.group(1))
                if bullet_match
                else len(numbered_match.group(1))
            )

            # Process list items at this level
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                if not stripped:
                    # Empty line - check if list continues
                    i += 1
                    if i >= len(lines):
                        break
                    # Peek at next line
                    next_stripped = lines[i].strip()
                    if not next_stripped:
                        continue
                    # Check if next line is a horizontal rule (---, ***, ___) - end the list
                    if re.match(r"^([-*_])\1{2,}\s*$", next_stripped):
                        # List ends at horizontal rule
                        break
                    # Check if next line is a list item at same or deeper level
                    next_bullet = re.match(r"^(\s*)[-*+]\s+", next_stripped)
                    next_numbered = re.match(r"^(\s*)(\d+)\.\s+", next_stripped)
                    if next_bullet or next_numbered:
                        next_indent = len(lines[i]) - len(lines[i].lstrip())
                        if next_indent >= base_indent:
                            # List continues
                            continue
                    # List ends
                    break

                # Check if this is a horizontal rule (---, ***, ___, * * *, - - -, _ _ _) - end the list
                if re.match(r"^([-*_])\1{2,}\s*$", stripped) or re.match(
                    r"^([-*_])(?:\s+\1){2,}\s*$", stripped
                ):
                    # List ends at horizontal rule
                    break

                # Check if this is a list item
                item_bullet = re.match(r"^(\s*)[-*+]\s+(.+)$", stripped)
                item_numbered = re.match(r"^(\s*)(\d+)\.\s+(.+)$", stripped)

                if not item_bullet and not item_numbered:
                    # Not a list item, end the list
                    break

                # Get indent level
                item_indent = (
                    len(item_bullet.group(1))
                    if item_bullet
                    else len(item_numbered.group(1))
                )

                if item_indent < base_indent:
                    # Indent decreased, we're done with this list
                    break

                if item_indent > base_indent:
                    # Nested item - should be handled by recursive call
                    break

                # Same level item
                content = (
                    item_bullet.group(2) if item_bullet else item_numbered.group(3)
                )
                i += 1

                # Collect nested content (deeper indented lines)
                nested_lines = []
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()

                    if not next_stripped:
                        # Empty line - check if list continues
                        nested_lines.append("")
                        i += 1
                        if i < len(lines):
                            peek_stripped = lines[i].strip()
                            if peek_stripped:
                                peek_indent = len(lines[i]) - len(lines[i].lstrip())
                                if peek_indent <= base_indent:
                                    # Next item is at same or higher level
                                    break
                        continue

                    next_indent = len(next_line) - len(next_line.lstrip())

                    if next_indent <= base_indent:
                        # Next line is at same or higher level, done with nested content
                        break

                    # This line is nested
                    nested_lines.append(next_line)
                    i += 1

                # Process nested content if any
                if nested_lines:
                    nested_html = _parse_lists(nested_lines)
                    nested_str = "\n".join(nested_html).strip()
                    if nested_str:
                        list_items.append(f"<li>{content}\n{nested_str}</li>")
                    else:
                        list_items.append(f"<li>{content}</li>")
                else:
                    list_items.append(f"<li>{content}</li>")

            # Output the list
            if list_items:
                result.append(
                    f"<{list_type}>\n" + "\n".join(list_items) + f"\n</{list_type}>"
                )
        else:
            # Not a list line, pass through
            result.append(original_line)
            i += 1

    return result


def markdown_to_html(markdown: str) -> str:
    """
    Convert markdown to HTML.
    Basic implementation - can be enhanced with markdown library later.

    Args:
        markdown: Markdown content string

    Returns:
        HTML string
    """
    if not markdown:
        return ""

    html = markdown

    # Code blocks ```code``` or ```language\ncode``` - do FIRST before other processing to preserve content
    # This regex handles:
    # - Optional language specifier after opening ``` (e.g., ```python)
    # - Multi-line code content
    # - Preserves whitespace and newlines
    code_blocks = []

    def replace_code_block(match):
        full_match = match.group(0)
        # Pattern matches: ```language\ncode``` or ```\ncode``` or ```code```
        # Group 1: optional language (word characters)
        # Group 2: code content (everything until closing ```)
        lang_match = re.match(r"```(\w+)?\s*\n?(.*?)```", full_match, re.DOTALL)
        if lang_match:
            lang = lang_match.group(1) or ""
            code_content = lang_match.group(2) if lang_match.group(2) else ""
            # Remove leading/trailing newlines from code content, but preserve internal whitespace
            code_content = code_content.strip("\n")
            # Preserve whitespace - HTML will render it with <pre>
            # Escape HTML entities in code content
            code_content = (
                code_content.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            # Store with placeholder - use format that won't match other regex patterns
            # Use angle brackets and numbers to avoid matching bold/italic/link patterns
            placeholder = f"<CODEBLOCK{len(code_blocks)}CODEBLOCK>"
            code_blocks.append((placeholder, lang, code_content))
            return placeholder
        return full_match

    # Find and replace all code blocks (non-greedy match to handle multiple blocks)
    # Pattern: ``` followed by optional language, optional whitespace/newline, then code content, then ```
    html = re.sub(r"```(\w+)?\s*\n?(.*?)```", replace_code_block, html, flags=re.DOTALL)

    # Tables (GFM syntax) - do before headers to avoid conflicts
    # Pattern: | Header | Header |\n|--------|--------|\n| Cell | Cell |
    # Tables must be protected from other processing
    tables = []

    def replace_table(match):
        full_match = match.group(0)
        # Parse table rows
        lines = [
            line.rstrip() for line in full_match.strip().split("\n") if line.strip()
        ]
        if len(lines) < 2:
            return full_match

        # First line is header
        header_line = lines[0]
        # Second line is separator (|----|----|) - skip it
        # Remaining lines are data rows

        # Extract header cells (split by |, filter empty strings from leading/trailing)
        header_parts = [p.strip() for p in header_line.split("|")]
        # Remove empty strings from start/end (markdown tables have | at start and end)
        header_cells = [p for p in header_parts if p]

        # Extract data rows (skip separator line at index 1)
        data_rows = []
        for line in lines[2:]:
            if not line.strip() or not line.strip().startswith("|"):
                break  # End of table
            cells_parts = [p.strip() for p in line.split("|")]
            cells = [p for p in cells_parts if p]
            if cells:
                data_rows.append(cells)

        # Build HTML table
        table_html = "<table>\n<thead>\n<tr>"
        for cell in header_cells:
            # Escape HTML in cell content
            cell_escaped = (
                cell.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            table_html += f"<th>{cell_escaped}</th>"
        table_html += "</tr>\n</thead>\n<tbody>"

        for row in data_rows:
            table_html += "\n<tr>"
            # Pad row to match header length if needed
            while len(row) < len(header_cells):
                row.append("")
            for cell in row[: len(header_cells)]:
                # Escape HTML in cell content
                cell_escaped = (
                    cell.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                table_html += f"<td>{cell_escaped}</td>"
            table_html += "</tr>"

        table_html += "\n</tbody>\n</table>"

        # Store with placeholder
        placeholder = f"<TABLEBLOCK{len(tables)}TABLEBLOCK>"
        tables.append((placeholder, table_html))
        return placeholder

    # Match GFM tables: lines starting with |, followed by separator line, then data rows
    # Pattern: | ... |\n|----|\n| ... |
    # More flexible pattern that handles various table formats
    table_pattern = re.compile(
        r"^\|.+\|\s*\n"  # Header row: | col1 | col2 |
        r"\|[-\s:]+(?:\|[-\s:]+)*\|\s*\n"  # Separator: |------|------| (one or more columns)
        r"(\|.+\|\s*\n?)+",  # Data rows: | cell1 | cell2 | (one or more rows)
        re.MULTILINE,
    )
    html = table_pattern.sub(replace_table, html)

    # Headers (H1-H6) - do after code blocks and tables to avoid conflicts
    # Add IDs to H2-H6 headings for TOC navigation (H1 is typically page title, not in TOC)
    def add_heading_id(match, level):
        heading_text = match.group(1)
        # Unescape backslashes in heading text (e.g., "1\. Title" -> "1. Title")
        # TurndownService escapes periods to prevent list interpretation, but we want them unescaped in HTML
        heading_text = heading_text.replace("\\.", ".")
        anchor = _generate_anchor(heading_text)
        return f'<h{level} id="{anchor}">{heading_text}</h{level}>'

    # Horizontal rules (---, ***, ___, * * *, - - -, _ _ _) - do before headers and lists to avoid conflicts
    # Pattern 1: three or more repeated dashes, asterisks, or underscores (---, ***, ___)
    # Pattern 2: three or more dashes, asterisks, or underscores separated by spaces (* * *, - - -, _ _ _)
    html = re.sub(r"^([-*_])\1{2,}\s*$", r"<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"^([-*_])(?:\s+\1){2,}\s*$", r"<hr>", html, flags=re.MULTILINE)

    # H1 headings - unescape backslashes (e.g., "1\. Title" -> "1. Title")
    def add_h1(match):
        heading_text = match.group(1).replace("\\.", ".")
        return f"<h1>{heading_text}</h1>"

    html = re.sub(r"^# (.+)$", add_h1, html, flags=re.MULTILINE)
    html = re.sub(
        r"^## (.+)$", lambda m: add_heading_id(m, 2), html, flags=re.MULTILINE
    )
    html = re.sub(
        r"^### (.+)$", lambda m: add_heading_id(m, 3), html, flags=re.MULTILINE
    )
    html = re.sub(
        r"^#### (.+)$", lambda m: add_heading_id(m, 4), html, flags=re.MULTILINE
    )
    html = re.sub(
        r"^##### (.+)$", lambda m: add_heading_id(m, 5), html, flags=re.MULTILINE
    )
    html = re.sub(
        r"^###### (.+)$", lambda m: add_heading_id(m, 6), html, flags=re.MULTILINE
    )

    # Parse lists (bullet and numbered) - handle nested lists
    # Do this BEFORE header conversion so we can parse markdown list syntax
    # But headers are already converted above, so we need to work with what we have
    # The list parser will skip lines that already have HTML tags
    lines = html.split("\n")
    lines = _parse_lists(lines)
    html = "\n".join(lines)

    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)

    # Italic
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"_(.+?)_", r"<em>\1</em>", html)

    # Links [text](url)
    html = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', html)

    # Images ![alt](url)
    html = re.sub(r"!\[([^\]]*)\]\(([^\)]+)\)", r'<img src="\2" alt="\1">', html)

    # Inline code `code` - do after other processing to avoid conflicts
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

    # Restore code blocks before paragraph processing
    # Use a unique marker that won't be split across lines
    for placeholder, lang, code_content in code_blocks:
        lang_attr = f' class="language-{lang}"' if lang else ""
        # Preserve newlines in code content - they'll be rendered by <pre>
        code_html = f"<pre><code{lang_attr}>{code_content}</code></pre>"
        html = html.replace(placeholder, code_html)

    # Restore tables before paragraph processing
    for placeholder, table_html in tables:
        html = html.replace(placeholder, table_html)

    # Paragraphs (lines not starting with #, *, -, <ul, <ol, <li, <pre, etc.)
    # Handle code blocks and tables carefully - they may span multiple lines after restoration
    # First, protect code blocks and tables by replacing them with placeholders
    code_block_pattern = re.compile(r"(<pre><code[^>]*>.*?</code></pre>)", re.DOTALL)
    table_pattern = re.compile(r"(<table>.*?</table>)", re.DOTALL)
    protected_blocks = []

    def protect_code_block(match):
        block = match.group(1)
        # Use placeholder format that won't match bold/italic/link patterns
        # Use a format that looks like an HTML tag so it's skipped by paragraph logic
        placeholder = f"<PROTECTEDCODE{len(protected_blocks)}PROTECTEDCODE>"
        protected_blocks.append((placeholder, block))
        return placeholder

    def protect_table(match):
        block = match.group(1)
        placeholder = f"<PROTECTEDTABLE{len(protected_blocks)}PROTECTEDTABLE>"
        protected_blocks.append((placeholder, block))
        return placeholder

    html = code_block_pattern.sub(protect_code_block, html)
    html = table_pattern.sub(protect_table, html)

    # Now split by newlines for paragraph processing
    lines = html.split("\n")
    result = []
    in_paragraph = False
    current_paragraph = []

    for line in lines:
        stripped = line.strip()

        # Check if this line contains a protected code block or table - must check before other processing
        if "<PROTECTEDCODE" in line or "<PROTECTEDTABLE" in line:
            if in_paragraph:
                result.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
                in_paragraph = False
            result.append(line)
            continue

        if not stripped:
            if in_paragraph:
                result.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
                in_paragraph = False
            result.append("")
        elif stripped.startswith(
            (
                "<h",
                "<p",
                "<pre",
                "<ul",
                "<ol",
                "<li",
                "<blockquote",
                "</ul",
                "</ol",
                "<table",
                "</table",
                "<hr",
                "<PROTECTEDCODE",
                "<PROTECTEDTABLE",
            )
        ):
            if in_paragraph:
                result.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
                in_paragraph = False
            result.append(line)
        else:
            in_paragraph = True
            current_paragraph.append(stripped)

    if in_paragraph and current_paragraph:
        result.append(f'<p>{" ".join(current_paragraph)}</p>')

    html = "\n".join(result)

    # Restore protected code blocks and tables - must happen after all processing
    for placeholder, block in protected_blocks:
        # Ensure blocks are on their own lines for proper paragraph separation
        html = html.replace(placeholder, f"\n{block}\n")

    # Final cleanup: remove excessive newlines but preserve structure
    html = re.sub(r"\n{3,}", "\n\n", html)

    # Post-process: wrap any remaining unwrapped text lines in paragraphs
    # This handles text that comes after tables/code blocks
    lines = html.split("\n")
    final_result = []
    current_text = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Empty line - flush any accumulated text
            if current_text:
                final_result.append(f'<p>{" ".join(current_text)}</p>')
                current_text = []
            final_result.append("")
        elif stripped.startswith(("<", "</")):
            # HTML tag - flush any accumulated text, then add the tag
            if current_text:
                final_result.append(f'<p>{" ".join(current_text)}</p>')
                current_text = []
            final_result.append(line)
        else:
            # Plain text - accumulate for paragraph
            current_text.append(stripped)

    # Flush any remaining text
    if current_text:
        final_result.append(f'<p>{" ".join(current_text)}</p>')

    return "\n".join(final_result)


def extract_internal_links(content: str) -> list:
    """
    Extract internal wiki links from markdown content.
    Supports formats: [text](slug), [text](slug#anchor), [text](/wiki/pages/slug)

    Args:
        content: Markdown content string

    Returns:
        List of link dictionaries with 'text' and 'target' (slug)
    """
    links = []
    if not content:
        return links

    # Pattern for markdown links: [text](target)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

    for match in link_pattern.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2)

        # Extract slug from various formats
        slug = _extract_slug_from_link(link_target)

        if slug:
            links.append(
                {
                    "text": link_text,
                    "target": slug,
                    "anchor": _extract_anchor_from_link(link_target),
                }
            )

    return links


def _extract_slug_from_link(link_target: str) -> Optional[str]:
    """Extract slug from link target (handles various formats)"""
    if not link_target:
        return None

    # Remove anchor if present: slug#anchor -> slug
    if "#" in link_target:
        link_target = link_target.split("#")[0]

    # Handle /wiki/pages/slug format
    if link_target.startswith("/wiki/pages/"):
        return link_target.replace("/wiki/pages/", "").strip("/")

    # Handle relative paths
    if link_target.startswith("./") or link_target.startswith("../"):
        # Extract filename without extension
        parts = link_target.split("/")
        filename = parts[-1]
        return filename.replace(".md", "")

    # Direct slug
    return link_target.strip("/")


def _extract_anchor_from_link(link_target: str) -> Optional[str]:
    """Extract anchor from link target if present"""
    if "#" in link_target:
        return link_target.split("#")[1]
    return None
