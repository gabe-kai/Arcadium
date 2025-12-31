"""Tests for comment API endpoints"""

import uuid

from app import db
from app.models.comment import Comment
from app.models.page import Page
from tests.test_api.conftest import auth_headers, mock_auth


def test_get_comments_empty(client, app, test_page):
    """Test getting comments for a page with no comments"""
    # Ensure page exists and is accessible
    with app.app_context():
        # Re-query to ensure page is in current session
        page = db.session.get(Page, test_page.id)
        if not page:
            # If not found, re-add it
            page = Page(
                title=test_page.title,
                slug=test_page.slug,
                content=test_page.content,
                created_by=test_page.created_by,
                updated_by=test_page.updated_by,
                status=test_page.status,
                section="Regression-Testing",
                file_path=test_page.file_path,
            )
            db.session.add(page)
            db.session.commit()
            page_id = str(page.id)
        else:
            page_id = str(page.id)

    response = client.get(f"/api/pages/{page_id}/comments")
    assert response.status_code == 200
    data = response.get_json()
    assert "comments" in data
    assert len(data["comments"]) == 0


def test_get_comments_with_comments(client, app, test_page, test_user_id):
    """Test getting comments for a page with comments"""
    with app.app_context():
        # Create a comment
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Test comment",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()

    page_id = str(test_page.id)
    response = client.get(f"/api/pages/{page_id}/comments")
    assert response.status_code == 200
    data = response.get_json()
    assert "comments" in data
    assert len(data["comments"]) == 1
    assert data["comments"][0]["content"] == "Test comment"


def test_get_comments_with_replies(client, app, test_page, test_user_id):
    """Test getting comments with nested replies"""
    with app.app_context():
        # Create a top-level comment
        parent = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Parent comment",
            thread_depth=1,
        )
        db.session.add(parent)
        db.session.flush()

        # Create a reply
        reply = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Reply comment",
            parent_comment_id=parent.id,
            thread_depth=2,
        )
        db.session.add(reply)
        db.session.commit()

    page_id = str(test_page.id)
    response = client.get(f"/api/pages/{page_id}/comments")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["comments"]) == 1
    assert len(data["comments"][0].get("replies", [])) == 1
    assert data["comments"][0]["replies"][0]["content"] == "Reply comment"


def test_get_comments_page_not_found(client):
    """Test getting comments for non-existent page"""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/pages/{fake_id}/comments")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_create_comment_requires_auth(client, test_page):
    """Test that creating a comment requires authentication"""
    page_id = str(test_page.id)
    response = client.post(
        f"/api/pages/{page_id}/comments", json={"content": "Test comment"}
    )
    assert response.status_code == 401


def test_create_comment_success(client, app, test_page, test_user_id):
    """Test successfully creating a comment"""
    with mock_auth(test_user_id, "player"):
        page_id = str(test_page.id)
        response = client.post(
            f"/api/pages/{page_id}/comments",
            json={"content": "Test comment", "is_recommendation": False},
            headers=auth_headers(test_user_id, "player"),
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["content"] == "Test comment"
        assert data["thread_depth"] == 1


def test_create_comment_missing_content(client, app, test_page, test_user_id):
    """Test creating a comment without content"""
    with mock_auth(test_user_id, "player"):
        page_id = str(test_page.id)
        response = client.post(
            f"/api/pages/{page_id}/comments",
            json={},
            headers=auth_headers(test_user_id, "player"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


def test_create_comment_viewer_forbidden(client, app, test_page, test_user_id):
    """Test that viewers cannot create comments"""
    with mock_auth(test_user_id, "viewer"):
        page_id = str(test_page.id)
        response = client.post(
            f"/api/pages/{page_id}/comments",
            json={"content": "Test comment"},
            headers=auth_headers(test_user_id, "viewer"),
        )
        assert response.status_code == 403


def test_create_reply(client, app, test_page, test_user_id):
    """Test creating a reply to a comment"""
    with app.app_context():
        # Create a parent comment
        parent = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Parent comment",
            thread_depth=1,
        )
        db.session.add(parent)
        db.session.commit()
        parent_id = str(parent.id)

    with mock_auth(test_user_id, "player"):
        page_id = str(test_page.id)
        response = client.post(
            f"/api/pages/{page_id}/comments",
            json={"content": "Reply comment", "parent_comment_id": parent_id},
            headers=auth_headers(test_user_id, "player"),
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["content"] == "Reply comment"
        assert data["thread_depth"] == 2
        assert data["parent_comment_id"] == parent_id


def test_create_reply_max_depth(client, app, test_page, test_user_id):
    """Test that replies cannot exceed max depth (5)"""
    with app.app_context():
        # Create a comment thread at max depth (5 levels)
        parent = None
        for depth in range(1, 6):
            comment = Comment(
                page_id=test_page.id,
                user_id=test_user_id,
                content=f"Comment at depth {depth}",
                parent_comment_id=parent.id if parent else None,
                thread_depth=depth,
            )
            db.session.add(comment)
            db.session.commit()
            parent = comment

        max_depth_comment_id = str(parent.id)

    with mock_auth(test_user_id, "player"):
        page_id = str(test_page.id)
        response = client.post(
            f"/api/pages/{page_id}/comments",
            json={
                "content": "This should fail",
                "parent_comment_id": max_depth_comment_id,
            },
            headers=auth_headers(test_user_id, "player"),
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Maximum comment thread depth" in data["error"]
        assert data["max_depth"] == 5


def test_update_comment_requires_auth(client, app, test_page, test_user_id):
    """Test that updating a comment requires authentication"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Original comment",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    response = client.put(
        f"/api/comments/{comment_id}", json={"content": "Updated comment"}
    )
    assert response.status_code == 401


def test_update_comment_success(client, app, test_page, test_user_id):
    """Test successfully updating a comment"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Original comment",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_user_id, "player"):
        response = client.put(
            f"/api/comments/{comment_id}",
            json={"content": "Updated comment"},
            headers=auth_headers(test_user_id, "player"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["content"] == "Updated comment"


def test_update_comment_wrong_owner(
    client, app, test_page, test_user_id, test_writer_id
):
    """Test that users cannot update other users' comments"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Original comment",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.put(
            f"/api/comments/{comment_id}",
            json={"content": "Updated comment"},
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data


def test_update_comment_admin_can_edit_any(
    client, app, test_page, test_user_id, test_admin_id
):
    """Test that admins can update any comment"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Original comment",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.put(
            f"/api/comments/{comment_id}",
            json={"content": "Updated by admin"},
            headers=auth_headers(test_admin_id, "admin"),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["content"] == "Updated by admin"


def test_delete_comment_requires_auth(client, app, test_page, test_user_id):
    """Test that deleting a comment requires authentication"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Comment to delete",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    response = client.delete(f"/api/comments/{comment_id}")
    assert response.status_code == 401


def test_delete_comment_success(client, app, test_page, test_user_id):
    """Test successfully deleting a comment"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Comment to delete",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_user_id, "player"):
        response = client.delete(
            f"/api/comments/{comment_id}", headers=auth_headers(test_user_id, "player")
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data

        # Verify comment is deleted
        with app.app_context():
            deleted = db.session.get(Comment, uuid.UUID(comment_id))
            assert deleted is None


def test_delete_comment_wrong_owner(
    client, app, test_page, test_user_id, test_writer_id
):
    """Test that users cannot delete other users' comments"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Comment to delete",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_writer_id, "writer"):
        response = client.delete(
            f"/api/comments/{comment_id}",
            headers=auth_headers(test_writer_id, "writer"),
        )
        assert response.status_code == 403


def test_delete_comment_admin_can_delete_any(
    client, app, test_page, test_user_id, test_admin_id
):
    """Test that admins can delete any comment"""
    with app.app_context():
        comment = Comment(
            page_id=test_page.id,
            user_id=test_user_id,
            content="Comment to delete",
            thread_depth=1,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = str(comment.id)

    with mock_auth(test_admin_id, "admin"):
        response = client.delete(
            f"/api/comments/{comment_id}", headers=auth_headers(test_admin_id, "admin")
        )
        assert response.status_code == 200

        # Verify comment is deleted
        with app.app_context():
            deleted = db.session.get(Comment, uuid.UUID(comment_id))
            assert deleted is None
