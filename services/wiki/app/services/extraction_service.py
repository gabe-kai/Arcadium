"""Service for extracting sections from pages into new pages"""

import re
import uuid
from typing import Dict, Optional

from app import db
from app.models.page import Page
from app.services.link_service import LinkService
from app.services.page_service import PageService
from app.services.version_service import VersionService
from app.utils.markdown_service import parse_frontmatter
from app.utils.toc_service import generate_toc


class ExtractionService:
    """Service for extracting sections from pages"""

    @staticmethod
    def extract_selection(
        page_id: uuid.UUID,
        selection_start: int,
        selection_end: int,
        new_title: str,
        new_slug: str,
        user_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        replace_with_link: bool = True,
    ) -> Dict:
        """
        Extract a text selection from a page into a new page.

        Args:
            page_id: ID of source page
            selection_start: Character position where selection starts
            selection_end: Character position where selection ends
            new_title: Title for the new page
            new_slug: Slug for the new page
            user_id: ID of user performing extraction
            parent_id: Optional parent page ID (defaults to source page)
            section: Optional section name
            replace_with_link: Whether to replace selection with link

        Returns:
            Dict with 'new_page' and 'original_page' info
        """
        # Get source page
        source_page = db.session.get(Page, page_id)
        if not source_page:
            raise ValueError(f"Page not found: {page_id}")

        # Parse frontmatter and get markdown content
        frontmatter, markdown_content = parse_frontmatter(source_page.content)

        # Validate selection bounds
        content_length = len(markdown_content)
        if (
            selection_start < 0
            or selection_end > content_length
            or selection_start >= selection_end
        ):
            raise ValueError("Invalid selection bounds")

        # Extract selected content
        extracted_content = markdown_content[selection_start:selection_end].strip()
        if not extracted_content:
            raise ValueError("Selected content is empty")

        # Determine parent (default to source page)
        if parent_id is None:
            parent_id = page_id

        # Create new page with extracted content
        new_page = PageService.create_page(
            title=new_title,
            content=extracted_content,
            user_id=user_id,
            slug=new_slug,
            parent_id=parent_id,
            section=section,
            status=source_page.status,  # Inherit status from source
        )

        # Replace selection with link if requested
        if replace_with_link:
            # Generate link text from first heading in extracted content, or use title
            link_text = ExtractionService._extract_link_text(
                extracted_content, new_title
            )
            link_markdown = f"[{link_text}]({new_slug})"

            # Replace selection with link
            new_content = (
                markdown_content[:selection_start]
                + link_markdown
                + markdown_content[selection_end:]
            )

            # Update source page
            PageService.update_page(
                page_id=page_id, user_id=user_id, content=new_content
            )

            # Create version with change summary
            VersionService.create_version(
                page_id=page_id,
                user_id=user_id,
                change_summary=f"Section extracted to {new_title}",
            )

            # Update links for source page (will create link to new page)
            LinkService.update_page_links(page_id, new_content)
        else:
            # Just update version without content change
            VersionService.create_version(
                page_id=page_id,
                user_id=user_id,
                change_summary=f"Section extracted to {new_title}",
            )

        # Create reverse link (from new page to source page)
        # Add a backlink reference in the new page's content
        new_page_content = new_page.content
        source_page_title = source_page.title
        source_page_slug = source_page.slug
        backlink_note = (
            f"\n\n---\n\n*See also: [{source_page_title}]({source_page_slug})*"
        )
        new_page_content_with_backlink = new_page_content + backlink_note

        # Update new page with backlink
        PageService.update_page(
            page_id=new_page.id, user_id=user_id, content=new_page_content_with_backlink
        )

        # Update links for new page (will create link back to source)
        LinkService.update_page_links(new_page.id, new_page_content_with_backlink)

        # Get updated source page
        source_page = db.session.get(Page, page_id)

        return {
            "new_page": {
                "id": str(new_page.id),
                "title": new_page.title,
                "slug": new_page.slug,
            },
            "original_page": {
                "id": str(source_page.id),
                "version": source_page.version,
            },
        }

    @staticmethod
    def extract_heading_section(
        page_id: uuid.UUID,
        heading_text: str,
        heading_level: int,
        new_title: str,
        new_slug: str,
        user_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
        section: Optional[str] = None,
        promote_as: str = "child",
    ) -> Dict:
        """
        Extract a heading section (heading + content until next heading) into a new page.

        Args:
            page_id: ID of source page
            heading_text: Text of the heading to extract
            heading_level: Level of the heading (2-6)
            new_title: Title for the new page
            new_slug: Slug for the new page
            user_id: ID of user performing extraction
            parent_id: Optional parent page ID
            section: Optional section name
            promote_as: "child" or "sibling" (determines parent if not specified)

        Returns:
            Dict with 'new_page' and 'original_page' info
        """
        # Get source page
        source_page = db.session.get(Page, page_id)
        if not source_page:
            raise ValueError(f"Page not found: {page_id}")

        # Parse frontmatter and get markdown content
        frontmatter, markdown_content = parse_frontmatter(source_page.content)

        # Find heading in content
        heading_pattern = re.compile(
            rf"^(#{{{heading_level}}})\s+{re.escape(heading_text)}\s*$",
            re.MULTILINE | re.IGNORECASE,
        )
        match = heading_pattern.search(markdown_content)

        if not match:
            raise ValueError(f"Heading not found: {heading_text}")

        heading_start = match.start()

        # Find end of section (next heading of same or higher level)
        section_end = ExtractionService._find_section_end(
            markdown_content, heading_start, heading_level
        )

        # Extract section content
        extracted_content = markdown_content[heading_start:section_end].strip()
        if not extracted_content:
            raise ValueError("Section content is empty")

        # Determine parent based on promote_as
        if parent_id is None:
            if promote_as == "child":
                parent_id = page_id
            elif promote_as == "sibling":
                parent_id = source_page.parent_id
            else:
                raise ValueError(f"Invalid promote_as value: {promote_as}")

        # Create new page
        new_page = PageService.create_page(
            title=new_title,
            content=extracted_content,
            user_id=user_id,
            slug=new_slug,
            parent_id=parent_id,
            section=section,
            status=source_page.status,
        )

        # Replace section with link
        link_text = new_title
        link_markdown = f"[{link_text}]({new_slug})"

        new_content = (
            markdown_content[:heading_start]
            + link_markdown
            + markdown_content[section_end:]
        )

        # Update source page
        PageService.update_page(page_id=page_id, user_id=user_id, content=new_content)

        # Create version with change summary
        VersionService.create_version(
            page_id=page_id,
            user_id=user_id,
            change_summary=f"Section '{heading_text}' extracted to {new_title}",
        )

        # Update links for source page (will create link to new page)
        LinkService.update_page_links(page_id, new_content)

        # Create reverse link (from new page to source page)
        # Add a backlink reference in the new page's content
        new_page_content = new_page.content
        source_page_title = source_page.title
        source_page_slug = source_page.slug
        backlink_note = (
            f"\n\n---\n\n*See also: [{source_page_title}]({source_page_slug})*"
        )
        new_page_content_with_backlink = new_page_content + backlink_note

        # Update new page with backlink
        PageService.update_page(
            page_id=new_page.id, user_id=user_id, content=new_page_content_with_backlink
        )

        # Update links for new page (will create link back to source)
        LinkService.update_page_links(new_page.id, new_page_content_with_backlink)

        # Get updated source page
        source_page = db.session.get(Page, page_id)

        return {
            "new_page": {
                "id": str(new_page.id),
                "title": new_page.title,
                "slug": new_page.slug,
            },
            "original_page": {
                "id": str(source_page.id),
                "version": source_page.version,
            },
        }

    @staticmethod
    def promote_section_from_toc(
        page_id: uuid.UUID,
        heading_anchor: str,
        new_title: str,
        new_slug: str,
        user_id: uuid.UUID,
        promote_as: str = "child",
        section: Optional[str] = None,
    ) -> Dict:
        """
        Promote a section from TOC (by anchor) into a new page.

        Args:
            page_id: ID of source page
            heading_anchor: Anchor ID of the heading (from TOC)
            new_title: Title for the new page
            new_slug: Slug for the new page
            user_id: ID of user performing extraction
            promote_as: "child" or "sibling"
            section: Optional section name

        Returns:
            Dict with 'new_page' and 'original_page' info
        """
        # Get source page
        source_page = db.session.get(Page, page_id)
        if not source_page:
            raise ValueError(f"Page not found: {page_id}")

        # Parse frontmatter and get markdown content
        frontmatter, markdown_content = parse_frontmatter(source_page.content)

        # Generate TOC to find heading by anchor
        toc = generate_toc(source_page.content)
        heading_info = None
        for entry in toc:
            if entry["anchor"] == heading_anchor:
                heading_info = entry
                break

        if not heading_info:
            raise ValueError(f"Heading with anchor '{heading_anchor}' not found")

        # Use extract_heading_section with the found heading
        return ExtractionService.extract_heading_section(
            page_id=page_id,
            heading_text=heading_info["text"],
            heading_level=heading_info["level"],
            new_title=new_title,
            new_slug=new_slug,
            user_id=user_id,
            parent_id=None,  # Will be determined by promote_as
            section=section,
            promote_as=promote_as,
        )

    @staticmethod
    def _find_section_end(content: str, heading_start: int, heading_level: int) -> int:
        """
        Find the end position of a section (next heading of same or higher level).

        Args:
            content: Markdown content
            heading_start: Start position of the heading
            heading_level: Level of the heading (2-6)

        Returns:
            End position of the section
        """
        # Search for next heading of same or higher level
        # Pattern matches headings from level 2 to heading_level
        pattern = re.compile(
            r"^(#{2," + str(heading_level) + r"})\s+(.+)$", re.MULTILINE
        )

        # Find all headings after the current one
        for match in pattern.finditer(content, heading_start + 1):
            match_level = len(match.group(1))
            if match_level <= heading_level:
                # Found next heading of same or higher level
                return match.start()

        # No next heading found, section goes to end of content
        return len(content)

    @staticmethod
    def _extract_link_text(content: str, fallback: str) -> str:
        """
        Extract link text from content (first heading, or fallback).

        Args:
            content: Markdown content
            fallback: Fallback text if no heading found

        Returns:
            Link text to use
        """
        # Look for first heading in content
        heading_pattern = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
        match = heading_pattern.search(content)

        if match:
            return match.group(1).strip()

        # No heading found, use fallback
        return fallback
