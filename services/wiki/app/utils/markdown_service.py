"""Markdown processing utilities"""
import re
import yaml
from typing import Dict, Optional, Tuple


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """
    Parse YAML frontmatter from markdown content.
    
    Args:
        content: Markdown content with optional YAML frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, markdown_content)
    """
    if not content.startswith('---'):
        return {}, content
    
    # Split on frontmatter delimiters
    parts = content.split('---', 2)
    
    if len(parts) < 3:
        # Malformed frontmatter, return as-is
        return {}, content
    
    frontmatter_str = parts[1].strip()
    markdown_content = parts[2].lstrip('\n')
    
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
            result.append('')
            i += 1
            continue
        
        # Check if this is a list item (bullet or numbered)
        bullet_match = re.match(r'^(\s*)[-*+]\s+(.+)$', stripped)
        numbered_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', stripped)
        
        if bullet_match or numbered_match:
            # Start of a list - collect all list items at this level
            list_items = []
            list_type = 'ul' if bullet_match else 'ol'
            base_indent = len(bullet_match.group(1)) if bullet_match else len(numbered_match.group(1))
            
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
                    # Check if next line is a list item at same or deeper level
                    next_bullet = re.match(r'^(\s*)[-*+]\s+', next_stripped)
                    next_numbered = re.match(r'^(\s*)(\d+)\.\s+', next_stripped)
                    if next_bullet or next_numbered:
                        next_indent = len(lines[i]) - len(lines[i].lstrip())
                        if next_indent >= base_indent:
                            # List continues
                            continue
                    # List ends
                    break
                
                # Check if this is a list item
                item_bullet = re.match(r'^(\s*)[-*+]\s+(.+)$', stripped)
                item_numbered = re.match(r'^(\s*)(\d+)\.\s+(.+)$', stripped)
                
                if not item_bullet and not item_numbered:
                    # Not a list item, end the list
                    break
                
                # Get indent level
                item_indent = len(item_bullet.group(1)) if item_bullet else len(item_numbered.group(1))
                
                if item_indent < base_indent:
                    # Indent decreased, we're done with this list
                    break
                
                if item_indent > base_indent:
                    # Nested item - should be handled by recursive call
                    break
                
                # Same level item
                content = item_bullet.group(2) if item_bullet else item_numbered.group(3)
                i += 1
                
                # Collect nested content (deeper indented lines)
                nested_lines = []
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    
                    if not next_stripped:
                        # Empty line - check if list continues
                        nested_lines.append('')
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
                    nested_str = '\n'.join(nested_html).strip()
                    if nested_str:
                        list_items.append(f'<li>{content}\n{nested_str}</li>')
                    else:
                        list_items.append(f'<li>{content}</li>')
                else:
                    list_items.append(f'<li>{content}</li>')
            
            # Output the list
            if list_items:
                result.append(f'<{list_type}>\n' + '\n'.join(list_items) + f'\n</{list_type}>')
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
        return ''
    
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
        lang_match = re.match(r'```(\w+)?\s*\n?(.*?)```', full_match, re.DOTALL)
        if lang_match:
            lang = lang_match.group(1) or ''
            code_content = lang_match.group(2) if lang_match.group(2) else ''
            # Remove leading/trailing newlines from code content, but preserve internal whitespace
            code_content = code_content.strip('\n')
            # Preserve whitespace - HTML will render it with <pre>
            # Escape HTML entities in code content
            code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Store with placeholder - use format that won't match other regex patterns
            # Use angle brackets and numbers to avoid matching bold/italic/link patterns
            placeholder = f'<CODEBLOCK{len(code_blocks)}CODEBLOCK>'
            code_blocks.append((placeholder, lang, code_content))
            return placeholder
        return full_match
    
    # Find and replace all code blocks (non-greedy match to handle multiple blocks)
    # Pattern: ``` followed by optional language, optional whitespace/newline, then code content, then ```
    html = re.sub(r'```(\w+)?\s*\n?(.*?)```', replace_code_block, html, flags=re.DOTALL)
    
    # Headers (H1-H6) - do after code blocks to avoid conflicts
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    
    # Parse lists (bullet and numbered) - handle nested lists
    # Do this BEFORE header conversion so we can parse markdown list syntax
    # But headers are already converted above, so we need to work with what we have
    # The list parser will skip lines that already have HTML tags
    lines = html.split('\n')
    lines = _parse_lists(lines)
    html = '\n'.join(lines)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # Links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Images ![alt](url)
    html = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'<img src="\2" alt="\1">', html)
    
    # Inline code `code` - do after other processing to avoid conflicts
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Restore code blocks before paragraph processing
    # Use a unique marker that won't be split across lines
    for placeholder, lang, code_content in code_blocks:
        lang_attr = f' class="language-{lang}"' if lang else ''
        # Preserve newlines in code content - they'll be rendered by <pre>
        code_html = f'<pre><code{lang_attr}>{code_content}</code></pre>'
        html = html.replace(placeholder, code_html)
    
    # Paragraphs (lines not starting with #, *, -, <ul, <ol, <li, <pre, etc.)
    # Handle code blocks carefully - they may span multiple lines after restoration
    # First, protect code blocks by replacing them with placeholders
    code_block_pattern = re.compile(r'(<pre><code[^>]*>.*?</code></pre>)', re.DOTALL)
    protected_blocks = []
    def protect_code_block(match):
        block = match.group(1)
        # Use placeholder format that won't match bold/italic/link patterns
        # Use a format that looks like an HTML tag so it's skipped by paragraph logic
        placeholder = f'<PROTECTEDCODE{len(protected_blocks)}PROTECTEDCODE>'
        protected_blocks.append((placeholder, block))
        return placeholder
    
    html = code_block_pattern.sub(protect_code_block, html)
    
    # Now split by newlines for paragraph processing
    lines = html.split('\n')
    result = []
    in_paragraph = False
    current_paragraph = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if this line contains a protected code block - must check before other processing
        if '<PROTECTEDCODE' in line:
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
            result.append('')
        elif stripped.startswith(('<h', '<p', '<pre', '<ul', '<ol', '<li', '<blockquote', '</ul', '</ol', '<PROTECTEDCODE')):
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
    
    html = '\n'.join(result)
    
    # Restore protected code blocks - must happen after all processing
    for placeholder, block in protected_blocks:
        html = html.replace(placeholder, block)
    
    return html


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
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    
    for match in link_pattern.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2)
        
        # Extract slug from various formats
        slug = _extract_slug_from_link(link_target)
        
        if slug:
            links.append({
                'text': link_text,
                'target': slug,
                'anchor': _extract_anchor_from_link(link_target)
            })
    
    return links


def _extract_slug_from_link(link_target: str) -> Optional[str]:
    """Extract slug from link target (handles various formats)"""
    if not link_target:
        return None
    
    # Remove anchor if present: slug#anchor -> slug
    if '#' in link_target:
        link_target = link_target.split('#')[0]
    
    # Handle /wiki/pages/slug format
    if link_target.startswith('/wiki/pages/'):
        return link_target.replace('/wiki/pages/', '').strip('/')
    
    # Handle relative paths
    if link_target.startswith('./') or link_target.startswith('../'):
        # Extract filename without extension
        parts = link_target.split('/')
        filename = parts[-1]
        return filename.replace('.md', '')
    
    # Direct slug
    return link_target.strip('/')


def _extract_anchor_from_link(link_target: str) -> Optional[str]:
    """Extract anchor from link target if present"""
    if '#' in link_target:
        return link_target.split('#')[1]
    return None

