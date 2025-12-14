"""Link service for managing page links"""
import uuid
from typing import List, Set, Optional
from app import db
from app.models.page import Page
from app.models.page_link import PageLink
from app.utils.markdown_service import extract_internal_links


class LinkService:
    """Service for managing bidirectional page links"""
    
    @staticmethod
    def extract_links_from_content(content: str) -> Set[str]:
        """
        Extract internal wiki links from markdown content.
        
        Supports multiple formats:
        - Standard markdown: [text](slug) or [text](/slug)
        - With anchors: [text](slug#anchor) or [text](/slug#anchor)
        - Wiki-style: [[slug]] or [[text|slug]]
        
        Args:
            content: Markdown content string
            
        Returns:
            Set of extracted slugs (without anchors or paths)
        """
        import re
        
        normalized_links = set()
        
        # Use the markdown service function for standard markdown links
        link_dicts = extract_internal_links(content)
        for link in link_dicts:
            slug = link.get('target')
            if slug:
                normalized_links.add(slug)
        
        # Also handle wiki-style links: [[slug]] or [[text|slug]]
        # Pattern matches: [[slug]] or [[text|slug]]
        # Group 1 captures the slug (either after | or the whole thing if no |)
        wiki_link_pattern = re.compile(r'\[\[(?:([^|\]]+)\|)?([^|\]]+)\]\]')
        for match in wiki_link_pattern.finditer(content):
            # If there's a pipe, group 2 is the slug; otherwise group 1 is the slug
            slug = match.group(2) if match.group(1) else match.group(1)
            if slug:
                # Normalize slug (lowercase, replace spaces with hyphens)
                slug = slug.strip().lower().replace(' ', '-')
                normalized_links.add(slug)
        
        return normalized_links
    
    @staticmethod
    def update_page_links(page_id: uuid.UUID, content: str) -> List[PageLink]:
        """
        Update bidirectional links for a page based on its content.
        Removes old links and creates new ones.
        
        Args:
            page_id: ID of the page
            content: Current markdown content of the page
            
        Returns:
            List of created PageLink instances
        """
        page = Page.query.get(page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Extract links from content
        linked_slugs = LinkService.extract_links_from_content(content)
        
        # Find linked pages by slug
        linked_pages = Page.query.filter(Page.slug.in_(linked_slugs)).all()
        linked_page_ids = {p.id for p in linked_pages}
        
        # Remove old links from this page
        PageLink.query.filter_by(from_page_id=page_id).delete()
        
        # Create new links
        new_links = []
        for linked_page in linked_pages:
            link = PageLink(
                from_page_id=page_id,
                to_page_id=linked_page.id,
                link_text=linked_page.title  # Default to page title
            )
            db.session.add(link)
            new_links.append(link)
        
        db.session.commit()
        
        return new_links
    
    @staticmethod
    def get_outgoing_links(page_id: uuid.UUID) -> List[Page]:
        """
        Get all pages that this page links to.
        
        Args:
            page_id: ID of the source page
            
        Returns:
            List of Page instances that are linked to
        """
        links = PageLink.query.filter_by(from_page_id=page_id).all()
        page_ids = [link.to_page_id for link in links]
        return Page.query.filter(Page.id.in_(page_ids)).all() if page_ids else []
    
    @staticmethod
    def get_incoming_links(page_id: uuid.UUID) -> List[Page]:
        """
        Get all pages that link to this page.
        
        Args:
            page_id: ID of the target page
            
        Returns:
            List of Page instances that link to this page
        """
        links = PageLink.query.filter_by(to_page_id=page_id).all()
        page_ids = [link.from_page_id for link in links]
        return Page.query.filter(Page.id.in_(page_ids)).all() if page_ids else []
    
    @staticmethod
    def handle_slug_change(old_slug: str, new_slug: str, page_id: uuid.UUID):
        """
        Handle link updates when a page's slug changes.
        Updates all pages that link to this page to use the new slug.
        
        Args:
            old_slug: Previous slug of the page
            new_slug: New slug of the page
            page_id: ID of the page whose slug changed
        """
        # Get all pages that link to this page
        incoming_links = PageLink.query.filter_by(to_page_id=page_id).all()
        
        if not incoming_links:
            return  # No pages link to this one
        
        # Get all pages that need updating
        from_page_ids = [link.from_page_id for link in incoming_links]
        pages_to_update = Page.query.filter(Page.id.in_(from_page_ids)).all()
        
        # Update content in each linking page
        for linking_page in pages_to_update:
            # Replace old slug with new slug in content
            # Handle various link formats
            content = linking_page.content
            
            # Replace in standard markdown links: [text](old-slug) -> [text](new-slug)
            import re
            # Pattern for [text](old-slug) or [text](/old-slug)
            pattern1 = re.compile(
                r'(\[([^\]]+)\]\(/?)({}(?:#[^\]]+)?)(\))'.format(re.escape(old_slug)),
                re.IGNORECASE
            )
            content = pattern1.sub(r'\1{}\4'.format(new_slug), content)
            
            # Replace in wiki-style links: [[old-slug]] -> [[new-slug]] or [[text|old-slug]] -> [[text|new-slug]]
            # Pattern matches: [[old-slug]] or [[text|old-slug]]
            # Group 1: [[
            # Group 2: optional text| part
            # Group 3: old-slug
            # Group 4: ]]
            pattern2 = re.compile(
                r'(\[\[)([^|\]]+\|)?({})(\]\])'.format(re.escape(old_slug)),
                re.IGNORECASE
            )
            # Replace: keep [[ and optional text|, replace slug, keep ]]
            def replace_wiki_link(match):
                prefix = match.group(1)  # [[
                text_part = match.group(2) or ''  # text| or empty
                suffix = match.group(4)  # ]]
                return f'{prefix}{text_part}{new_slug}{suffix}'
            content = pattern2.sub(replace_wiki_link, content)
            
            # Update page content
            linking_page.content = content
            db.session.commit()
            
            # Re-extract and update links for the linking page
            LinkService.update_page_links(linking_page.id, content)
    
    @staticmethod
    def handle_page_deletion(page_id: uuid.UUID):
        """
        Clean up links when a page is deleted.
        Removes all incoming and outgoing links for the page.
        
        Args:
            page_id: ID of the page being deleted
        """
        # Delete all links from this page
        PageLink.query.filter_by(from_page_id=page_id).delete()
        
        # Delete all links to this page
        PageLink.query.filter_by(to_page_id=page_id).delete()
        
        db.session.commit()
    
    @staticmethod
    def get_link_statistics(page_id: uuid.UUID) -> dict:
        """
        Get link statistics for a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            Dict with incoming and outgoing link counts
        """
        incoming_count = PageLink.query.filter_by(to_page_id=page_id).count()
        outgoing_count = PageLink.query.filter_by(from_page_id=page_id).count()
        
        return {
            'incoming_links': incoming_count,
            'outgoing_links': outgoing_count,
            'total_links': incoming_count + outgoing_count
        }
    
    @staticmethod
    def find_broken_links(page_id: Optional[uuid.UUID] = None) -> List[dict]:
        """
        Find broken links (links to non-existent pages).
        
        Args:
            page_id: Optional page ID to check. If None, checks all pages.
            
        Returns:
            List of dicts with broken link information
        """
        broken_links = []
        
        if page_id:
            # Check links from specific page
            links = PageLink.query.filter_by(from_page_id=page_id).all()
            for link in links:
                target_page = Page.query.get(link.to_page_id)
                if not target_page:
                    broken_links.append({
                        'from_page_id': str(link.from_page_id),
                        'to_page_id': str(link.to_page_id),
                        'link_text': link.link_text
                    })
        else:
            # Check all links
            all_links = PageLink.query.all()
            for link in all_links:
                target_page = Page.query.get(link.to_page_id)
                if not target_page:
                    broken_links.append({
                        'from_page_id': str(link.from_page_id),
                        'to_page_id': str(link.to_page_id),
                        'link_text': link.link_text
                    })
        
        return broken_links

