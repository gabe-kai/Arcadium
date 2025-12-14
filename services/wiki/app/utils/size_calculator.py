"""Utilities for calculating page size and word count"""
import re


def calculate_word_count(content: str) -> int:
    """
    Calculate word count from markdown content.
    Excludes images (markdown image syntax) from count.
    
    Args:
        content: Markdown content string
        
    Returns:
        Word count (integer)
    """
    if not content:
        return 0
    
    # Remove YAML frontmatter if present
    content = _remove_frontmatter(content)
    
    # Remove markdown image syntax: ![alt](url) or ![alt](url "title")
    content = re.sub(r'!\[.*?\]\([^\)]+\)', '', content)
    
    # Remove markdown links but keep the text: [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    
    # Remove markdown formatting but keep text
    content = re.sub(r'[#*_`~]', '', content)  # Headers, bold, italic, code
    content = re.sub(r'\[|\]', '', content)  # Remaining brackets
    
    # Remove HTML tags if any
    content = re.sub(r'<[^>]+>', '', content)
    
    # Split into words (whitespace-separated)
    words = re.findall(r'\b\w+\b', content)
    
    return len(words)


def calculate_content_size_kb(content: str) -> float:
    """
    Calculate content size in kilobytes.
    Excludes images (only counts text content).
    
    Args:
        content: Markdown content string
        
    Returns:
        Size in kilobytes (float)
    """
    if not content:
        return 0.0
    
    # Remove YAML frontmatter if present
    content = _remove_frontmatter(content)
    
    # Remove markdown image syntax (images don't count toward size)
    content = re.sub(r'!\[.*?\]\([^\)]+\)', '', content)
    
    # Calculate size in bytes (UTF-8 encoding)
    size_bytes = len(content.encode('utf-8'))
    
    # Convert to kilobytes
    return round(size_bytes / 1024.0, 2)


def _remove_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from content if present"""
    if content.startswith('---'):
        # Find the closing ---
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2].lstrip('\n')
    return content

