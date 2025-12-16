"""File scanner for finding markdown files"""
import os
from pathlib import Path
from typing import List, Optional
from flask import current_app


class FileScanner:
    """Scans for markdown files in the pages directory"""
    
    @staticmethod
    def scan_directory(directory: Optional[str] = None) -> List[str]:
        """
        Scan directory for all .md files.
        
        Args:
            directory: Directory to scan (defaults to WIKI_PAGES_DIR)
            
        Returns:
            List of file paths relative to pages directory
        """
        if directory is None:
            directory = current_app.config.get('WIKI_PAGES_DIR', 'data/pages')
        
        if not os.path.exists(directory):
            return []
        
        markdown_files = []
        
        # Walk through directory recursively
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    # Get relative path from pages directory
                    rel_path = os.path.relpath(full_path, directory)
                    # Normalize to forward slashes for cross-platform compatibility
                    rel_path = rel_path.replace('\\', '/')
                    markdown_files.append(rel_path)
        
        return sorted(markdown_files)
    
    @staticmethod
    def scan_file(file_path: str, base_directory: Optional[str] = None) -> Optional[str]:
        """
        Check if a specific file exists and return its relative path.
        
        Args:
            file_path: File path (can be absolute or relative)
            base_directory: Base directory for relative paths (defaults to WIKI_PAGES_DIR)
            
        Returns:
            Relative path if file exists, None otherwise
        """
        if base_directory is None:
            base_directory = current_app.config.get('WIKI_PAGES_DIR', 'data/pages')
        
        # If file_path is already relative, use it as-is
        if os.path.isabs(file_path):
            # Absolute path - check if it's within base_directory
            if not file_path.startswith(base_directory):
                return None
            rel_path = os.path.relpath(file_path, base_directory)
        else:
            # Relative path
            rel_path = file_path
        
        # Normalize to forward slashes for cross-platform compatibility
        rel_path = rel_path.replace('\\', '/')
        
        full_path = os.path.join(base_directory, rel_path)
        
        if os.path.exists(full_path) and full_path.endswith('.md'):
            return rel_path
        
        return None
    
    @staticmethod
    def get_file_modification_time(file_path: str, base_directory: Optional[str] = None) -> Optional[float]:
        """
        Get file modification time.
        
        Args:
            file_path: Relative file path
            base_directory: Base directory (defaults to WIKI_PAGES_DIR)
            
        Returns:
            Modification time as float (Unix timestamp), or None if file doesn't exist
        """
        if base_directory is None:
            base_directory = current_app.config.get('WIKI_PAGES_DIR', 'data/pages')
        
        full_path = os.path.join(base_directory, file_path)
        
        if os.path.exists(full_path):
            return os.path.getmtime(full_path)
        
        return None

