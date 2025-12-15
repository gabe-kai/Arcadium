"""Comment service for managing page comments"""
import uuid
from typing import Optional, List, Dict
from app import db
from app.models.comment import Comment
from app.models.page import Page


class CommentService:
    """Service for managing wiki page comments"""
    
    MAX_THREAD_DEPTH = 5
    
    @staticmethod
    def get_comments(page_id: uuid.UUID, include_replies: bool = True) -> List[Dict]:
        """
        Get all comments for a page, optionally including nested replies.
        
        Args:
            page_id: ID of the page
            include_replies: Whether to include nested replies in the response
            
        Returns:
            List of comment dictionaries with nested replies
        """
        # Get all top-level comments (no parent)
        top_level_comments = db.session.query(Comment).filter_by(
            page_id=page_id,
            parent_comment_id=None
        ).order_by(Comment.created_at.asc()).all()
        
        comments_list = []
        for comment in top_level_comments:
            comment_dict = CommentService._comment_to_dict(comment)
            if include_replies:
                comment_dict['replies'] = CommentService._get_replies(comment.id)
            comments_list.append(comment_dict)
        
        return comments_list
    
    @staticmethod
    def _get_replies(parent_comment_id: uuid.UUID) -> List[Dict]:
        """
        Recursively get all replies to a comment.
        
        Args:
            parent_comment_id: ID of the parent comment
            
        Returns:
            List of reply dictionaries (nested)
        """
        replies = db.session.query(Comment).filter_by(
            parent_comment_id=parent_comment_id
        ).order_by(Comment.created_at.asc()).all()
        
        replies_list = []
        for reply in replies:
            reply_dict = CommentService._comment_to_dict(reply)
            # Recursively get nested replies
            reply_dict['replies'] = CommentService._get_replies(reply.id)
            replies_list.append(reply_dict)
        
        return replies_list
    
    @staticmethod
    def _comment_to_dict(comment: Comment) -> Dict:
        """
        Convert a Comment model to a dictionary with user info.
        
        Args:
            comment: Comment model instance
            
        Returns:
            Dictionary representation of the comment
        """
        # Note: In production, user info would come from Auth Service
        # For now, we'll use a placeholder structure
        return {
            'id': str(comment.id),
            'user': {
                'id': str(comment.user_id),
                'username': 'user'  # Would be fetched from Auth Service
            },
            'content': comment.content,
            'is_recommendation': comment.is_recommendation,
            'parent_comment_id': str(comment.parent_comment_id) if comment.parent_comment_id else None,
            'thread_depth': comment.thread_depth,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'updated_at': comment.updated_at.isoformat() if comment.updated_at else None
        }
    
    @staticmethod
    def create_comment(
        page_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        is_recommendation: bool = False,
        parent_comment_id: Optional[uuid.UUID] = None
    ) -> Comment:
        """
        Create a new comment or reply.
        
        Args:
            page_id: ID of the page
            user_id: ID of the user creating the comment
            content: Comment text
            is_recommendation: Whether this is a recommendation
            parent_comment_id: Optional parent comment ID for replies
            
        Returns:
            Created Comment instance
            
        Raises:
            ValueError: If page not found, max depth reached, or validation fails
        """
        # Verify page exists
        page = db.session.get(Page, page_id)
        if not page:
            raise ValueError(f"Page not found: {page_id}")
        
        # Calculate thread depth
        thread_depth = 1
        if parent_comment_id:
            parent_comment = db.session.get(Comment, parent_comment_id)
            if not parent_comment:
                raise ValueError(f"Parent comment not found: {parent_comment_id}")
            
            if parent_comment.page_id != page_id:
                raise ValueError("Parent comment must be on the same page")
            
            thread_depth = parent_comment.thread_depth + 1
            
            # Check max depth
            if thread_depth > CommentService.MAX_THREAD_DEPTH:
                raise ValueError(
                    f"Maximum comment thread depth ({CommentService.MAX_THREAD_DEPTH}) reached. "
                    f"Current depth: {parent_comment.thread_depth}"
                )
        
        # Create comment
        comment = Comment(
            page_id=page_id,
            user_id=user_id,
            content=content,
            is_recommendation=is_recommendation,
            parent_comment_id=parent_comment_id,
            thread_depth=thread_depth
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return comment
    
    @staticmethod
    def update_comment(comment_id: uuid.UUID, user_id: uuid.UUID, content: str, user_role: str = 'viewer') -> Comment:
        """
        Update a comment.
        
        Args:
            comment_id: ID of the comment to update
            user_id: ID of the user (for permission check)
            content: New comment content
            user_role: Role of the user (for admin bypass)
            
        Returns:
            Updated Comment instance
            
        Raises:
            ValueError: If comment not found or user doesn't have permission
        """
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError(f"Comment not found: {comment_id}")
        
        # Check permission (owner or admin)
        if comment.user_id != user_id and user_role != 'admin':
            raise ValueError("You can only update your own comments")
        
        comment.content = content
        db.session.commit()
        
        return comment
    
    @staticmethod
    def delete_comment(comment_id: uuid.UUID, user_id: uuid.UUID, user_role: str = 'viewer') -> None:
        """
        Delete a comment.
        
        Args:
            comment_id: ID of the comment to delete
            user_id: ID of the user (for permission check)
            user_role: Role of the user (for admin bypass)
            
        Raises:
            ValueError: If comment not found or user doesn't have permission
        """
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError(f"Comment not found: {comment_id}")
        
        # Check permission (owner or admin)
        if comment.user_id != user_id and user_role != 'admin':
            raise ValueError("You can only delete your own comments")
        
        # CASCADE will handle deleting replies
        db.session.delete(comment)
        db.session.commit()

