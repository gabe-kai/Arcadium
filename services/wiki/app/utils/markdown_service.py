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
    
    # Headers (H1-H6)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    
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
    
    # Code blocks ```code```
    html = re.sub(r'```([^`]+)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
    
    # Inline code `code`
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Paragraphs (lines not starting with #, *, -, etc.)
    lines = html.split('\n')
    result = []
    in_paragraph = False
    current_paragraph = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_paragraph:
                result.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
                in_paragraph = False
            result.append('')
        elif stripped.startswith(('<h', '<p', '<pre', '<ul', '<ol', '<li')):
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
    
    return '\n'.join(result)


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

