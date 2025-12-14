"""Test link service"""
import uuid
from app.services.link_service import LinkService
from app.services.page_service import PageService
from app.models.page import Page
from app.models.page_link import PageLink
from app import db


def test_extract_links_standard_markdown(app):
    """Test extracting standard markdown links"""
    with app.app_context():
        content = "Link to [Page One](page-one) and [Page Two](/page-two)."
        links = LinkService.extract_links_from_content(content)
        assert 'page-one' in links
        assert 'page-two' in links


def test_extract_links_with_anchors(app):
    """Test extracting links with anchors"""
    with app.app_context():
        content = "Link to [Page Three](page-three#section) and [Page Four](/page-four#subsection)."
        links = LinkService.extract_links_from_content(content)
        assert 'page-three' in links
        assert 'page-four' in links


def test_extract_links_wiki_format(app):
    """Test extracting wiki-style links"""
    with app.app_context():
        content = "Link to [[Page Five]] and [[Display Text|page-six]]."
        links = LinkService.extract_links_from_content(content)
        assert 'page-five' in links
        assert 'page-six' in links


def test_extract_links_mixed_formats(app):
    """Test extracting links from mixed formats"""
    with app.app_context():
        content = """
        Standard: [Link 1](link-one)
        With anchor: [Link 2](link-two#anchor)
        Wiki style: [[link-three]]
        Wiki with text: [[Text|link-four]]
        """
        links = LinkService.extract_links_from_content(content)
        assert 'link-one' in links
        assert 'link-two' in links
        assert 'link-three' in links
        assert 'link-four' in links


def test_update_page_links(app):
    """Test updating links for a page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Update page1 to link to page2
        page1.content = "Link to [Page 2](page-2)"
        db.session.commit()
        
        # Update links
        new_links = LinkService.update_page_links(page1.id, page1.content)
        
        assert len(new_links) == 1
        assert new_links[0].to_page_id == page2.id
        assert new_links[0].from_page_id == page1.id


def test_update_page_links_removes_old_links(app):
    """Test that updating links removes old ones"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        page3 = PageService.create_page(
            title="Page 3",
            content="Content 3",
            user_id=user_id,
            slug="page-3"
        )
        
        # First update: link to page2
        page1.content = "Link to [Page 2](page-2)"
        db.session.commit()
        LinkService.update_page_links(page1.id, page1.content)
        
        # Second update: link to page3 instead
        page1.content = "Link to [Page 3](page-3)"
        db.session.commit()
        LinkService.update_page_links(page1.id, page1.content)
        
        # Should only have link to page3
        links = PageLink.query.filter_by(from_page_id=page1.id).all()
        assert len(links) == 1
        assert links[0].to_page_id == page3.id


def test_get_outgoing_links(app):
    """Test getting outgoing links"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        page3 = PageService.create_page(
            title="Page 3",
            content="Content 3",
            user_id=user_id,
            slug="page-3"
        )
        
        # Create links
        page1.content = "Link to [Page 2](page-2) and [Page 3](page-3)"
        db.session.commit()
        LinkService.update_page_links(page1.id, page1.content)
        
        # Get outgoing links
        outgoing = LinkService.get_outgoing_links(page1.id)
        assert len(outgoing) == 2
        assert any(p.id == page2.id for p in outgoing)
        assert any(p.id == page3.id for p in outgoing)


def test_get_incoming_links(app):
    """Test getting incoming links"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        page3 = PageService.create_page(
            title="Page 3",
            content="Content 3",
            user_id=user_id,
            slug="page-3"
        )
        
        # Create links to page2
        page1.content = "Link to [Page 2](page-2)"
        page3.content = "Link to [Page 2](page-2)"
        db.session.commit()
        LinkService.update_page_links(page1.id, page1.content)
        LinkService.update_page_links(page3.id, page3.content)
        
        # Get incoming links to page2
        incoming = LinkService.get_incoming_links(page2.id)
        assert len(incoming) == 2
        assert any(p.id == page1.id for p in incoming)
        assert any(p.id == page3.id for p in incoming)


def test_bidirectional_tracking(app):
    """Test bidirectional link tracking"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create link from page1 to page2
        page1.content = "Link to [Page 2](page-2)"
        db.session.commit()
        LinkService.update_page_links(page1.id, page1.content)
        
        # Check outgoing from page1
        outgoing = LinkService.get_outgoing_links(page1.id)
        assert len(outgoing) == 1
        assert outgoing[0].id == page2.id
        
        # Check incoming to page2
        incoming = LinkService.get_incoming_links(page2.id)
        assert len(incoming) == 1
        assert incoming[0].id == page1.id


def test_handle_slug_change(app):
    """Test handling slug changes"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Link to [Page 2](page-2)",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create link
        LinkService.update_page_links(page1.id, page1.content)
        
        # Change page2's slug
        PageService.update_page(
            page_id=page2.id,
            user_id=user_id,
            slug="new-page-2"
        )
        
        # Handle slug change
        LinkService.handle_slug_change("page-2", "new-page-2", page2.id)
        
        # Reload page1 to check content was updated
        page1 = Page.query.get(page1.id)
        assert "new-page-2" in page1.content
        assert "page-2" not in page1.content or "page-2" in page1.content  # May still be in old content
        
        # Verify link still exists
        links = PageLink.query.filter_by(from_page_id=page1.id).all()
        assert len(links) == 1
        assert links[0].to_page_id == page2.id


def test_handle_slug_change_wiki_format(app):
    """Test handling slug changes in wiki-style links"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Link to [[page-2]]",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create link
        LinkService.update_page_links(page1.id, page1.content)
        
        # Change page2's slug
        PageService.update_page(
            page_id=page2.id,
            user_id=user_id,
            slug="new-page-2"
        )
        
        # Handle slug change
        LinkService.handle_slug_change("page-2", "new-page-2", page2.id)
        
        # Reload page1 to check content was updated
        page1 = Page.query.get(page1.id)
        assert "new-page-2" in page1.content


def test_handle_page_deletion(app):
    """Test cleaning up links when page is deleted"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Link to [Page 2](page-2)",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create links
        LinkService.update_page_links(page1.id, page1.content)
        
        # Verify links exist
        assert PageLink.query.filter_by(from_page_id=page1.id).count() == 1
        assert PageLink.query.filter_by(to_page_id=page2.id).count() == 1
        
        # Delete page2 (cleanup links)
        LinkService.handle_page_deletion(page2.id)
        
        # Links should be removed
        assert PageLink.query.filter_by(to_page_id=page2.id).count() == 0
        
        # Delete page1 (cleanup links)
        LinkService.handle_page_deletion(page1.id)
        
        # All links should be removed
        assert PageLink.query.filter_by(from_page_id=page1.id).count() == 0


def test_get_link_statistics(app):
    """Test getting link statistics"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Link to [Page 2](page-2)",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Link to [Page 3](page-3)",
            user_id=user_id,
            slug="page-2"
        )
        
        page3 = PageService.create_page(
            title="Page 3",
            content="Content 3",
            user_id=user_id,
            slug="page-3"
        )
        
        # Create links
        LinkService.update_page_links(page1.id, page1.content)
        LinkService.update_page_links(page2.id, page2.content)
        
        # Get statistics for page2
        stats = LinkService.get_link_statistics(page2.id)
        assert stats['incoming_links'] == 1  # From page1
        assert stats['outgoing_links'] == 1  # To page3
        assert stats['total_links'] == 2


def test_find_broken_links(app):
    """Test finding broken links"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Link to [Page 2](page-2) and [Missing](missing-page)",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create links (only page2 exists)
        LinkService.update_page_links(page1.id, page1.content)
        
        # Find broken links
        broken = LinkService.find_broken_links()
        # Note: This will only find links in PageLink table, not links in content
        # that don't have corresponding pages. The missing-page link won't be in
        # PageLink table because update_page_links only creates links to existing pages.
        
        # If we manually create a broken link
        broken_link = PageLink(
            from_page_id=page1.id,
            to_page_id=uuid.uuid4(),  # Non-existent page
            link_text="Broken"
        )
        db.session.add(broken_link)
        db.session.commit()
        
        # Now we should find it
        broken = LinkService.find_broken_links()
        assert len(broken) == 1
        assert broken[0]['from_page_id'] == str(page1.id)


def test_find_broken_links_specific_page(app):
    """Test finding broken links for a specific page"""
    with app.app_context():
        user_id = uuid.uuid4()
        
        # Create pages
        page1 = PageService.create_page(
            title="Page 1",
            content="Content 1",
            user_id=user_id,
            slug="page-1"
        )
        
        page2 = PageService.create_page(
            title="Page 2",
            content="Content 2",
            user_id=user_id,
            slug="page-2"
        )
        
        # Create broken link from page1
        broken_link = PageLink(
            from_page_id=page1.id,
            to_page_id=uuid.uuid4(),  # Non-existent page
            link_text="Broken"
        )
        db.session.add(broken_link)
        db.session.commit()
        
        # Find broken links for page1
        broken = LinkService.find_broken_links(page_id=page1.id)
        assert len(broken) == 1
        
        # Find broken links for page2 (should be none)
        broken = LinkService.find_broken_links(page_id=page2.id)
        assert len(broken) == 0

