"""Navigation service for wiki pages"""

import uuid
from typing import Dict, List, Optional

from app import db
from app.models.page import Page


class NavigationService:
    """Service for navigation-related operations"""

    @staticmethod
    def get_navigation_tree(
        user_role: str = "viewer", user_id: Optional[uuid.UUID] = None
    ) -> List[Dict]:
        """
        Get the full page hierarchy as a navigation tree.

        Args:
            user_role: Role of requesting user (for draft filtering)
            user_id: Optional user ID (for draft filtering)

        Returns:
            List of root pages with nested children
        """
        # Get all root pages (no parent)
        query = Page.query.filter(Page.parent_id.is_(None))

        # Filter drafts based on permissions
        if user_role == "admin":
            # Admins see all pages (published and drafts)
            pass  # No filtering needed
        elif user_role == "writer":
            if user_id:
                # Show published + own drafts
                from sqlalchemy import and_, or_

                query = query.filter(
                    or_(
                        Page.status == "published",
                        and_(Page.status == "draft", Page.created_by == user_id),
                    )
                )
            else:
                # No user ID, only published
                query = query.filter_by(status="published")
        else:
            # Viewers/players only see published
            query = query.filter_by(status="published")

        root_pages = query.order_by(Page.order_index, Page.title).all()

        # Build tree recursively
        tree = []
        for page in root_pages:
            tree.append(NavigationService._build_page_node(page, user_role, user_id))

        return tree

    @staticmethod
    def _build_page_node(
        page: Page, user_role: str = "viewer", user_id: Optional[uuid.UUID] = None
    ) -> Dict:
        """
        Build a page node with its children recursively.

        Args:
            page: Page instance
            user_role: Role of requesting user
            user_id: Optional user ID

        Returns:
            Dictionary representation of page with children
        """
        node = {
            "id": str(page.id),
            "title": page.title,
            "slug": page.slug,
            "status": page.status,
            "section": page.section,
        }

        # Get children
        query = Page.query.filter_by(parent_id=page.id)

        # Filter drafts based on permissions
        if user_role == "admin":
            # Admins see all pages (published and drafts)
            pass  # No filtering needed
        elif user_role == "writer":
            if user_id:
                from sqlalchemy import and_, or_

                query = query.filter(
                    or_(
                        Page.status == "published",
                        and_(Page.status == "draft", Page.created_by == user_id),
                    )
                )
            else:
                query = query.filter_by(status="published")
        else:
            query = query.filter_by(status="published")

        children = query.order_by(Page.order_index, Page.title).all()

        # Recursively build children
        node["children"] = [
            NavigationService._build_page_node(child, user_role, user_id)
            for child in children
        ]

        return node

    @staticmethod
    def get_breadcrumb(page_id: uuid.UUID) -> List[Dict]:
        """
        Get breadcrumb path from root to the specified page.

        Args:
            page_id: ID of the page

        Returns:
            List of pages from root to current page

        Raises:
            ValueError: If page not found
        """
        page = db.session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")

        breadcrumb = []
        current = page

        # Build path from current page up to root
        visited = set()  # Prevent infinite loops
        while current and current.id not in visited:
            visited.add(current.id)
            breadcrumb.insert(
                0, {"id": str(current.id), "title": current.title, "slug": current.slug}
            )

            if current.parent_id:
                current = db.session.get(Page, current.parent_id)
            else:
                break

        return breadcrumb

    @staticmethod
    def get_previous_next(
        page_id: uuid.UUID,
        user_role: str = "viewer",
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict:
        """
        Get previous and next pages in the same parent's children list.

        Args:
            page_id: ID of the current page
            user_role: Role of requesting user (for draft filtering)
            user_id: Optional user ID (for draft filtering)

        Returns:
            Dictionary with 'previous' and 'next' page info (or None)

        Raises:
            ValueError: If page not found
        """
        page = db.session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")

        # Get siblings (pages with same parent)
        query = Page.query.filter_by(parent_id=page.parent_id)

        # Filter drafts based on permissions
        if user_role == "admin":
            # Admins see all pages (published and drafts)
            pass  # No filtering needed
        elif user_role == "writer":
            if user_id:
                from sqlalchemy import and_, or_

                query = query.filter(
                    or_(
                        Page.status == "published",
                        and_(Page.status == "draft", Page.created_by == user_id),
                    )
                )
            else:
                query = query.filter_by(status="published")
        else:
            query = query.filter_by(status="published")

        siblings = query.order_by(Page.order_index, Page.title).all()

        # Find current page index
        current_index = None
        for i, sibling in enumerate(siblings):
            if sibling.id == page.id:
                current_index = i
                break

        result = {"previous": None, "next": None}

        if current_index is not None:
            # Get previous page
            if current_index > 0:
                prev_page = siblings[current_index - 1]
                result["previous"] = {
                    "id": str(prev_page.id),
                    "title": prev_page.title,
                    "slug": prev_page.slug,
                }

            # Get next page
            if current_index < len(siblings) - 1:
                next_page = siblings[current_index + 1]
                result["next"] = {
                    "id": str(next_page.id),
                    "title": next_page.title,
                    "slug": next_page.slug,
                }

        return result
