"""Section extraction endpoints"""
import uuid
from flask import Blueprint, request, jsonify
from app import db
from app.models.page import Page
from app.middleware.auth import require_auth, require_role
from app.services.extraction_service import ExtractionService

extraction_bp = Blueprint('extraction', __name__)


@extraction_bp.route('/pages/<uuid:page_id>/extract', methods=['POST'])
@require_auth
@require_role(['writer', 'admin'])
def extract_selection(page_id):
    """
    Extract a text selection from a page into a new page.
    
    Permissions: Writer, Admin
    """
    try:
        user_id = request.user_id
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        selection_start = data.get('selection_start')
        selection_end = data.get('selection_end')
        new_title = data.get('new_title')
        new_slug = data.get('new_slug')
        
        if selection_start is None or selection_end is None:
            return jsonify({'error': 'selection_start and selection_end are required'}), 400
        if not new_title:
            return jsonify({'error': 'new_title is required'}), 400
        if not new_slug:
            return jsonify({'error': 'new_slug is required'}), 400
        
        # Convert to integers
        try:
            selection_start = int(selection_start)
            selection_end = int(selection_end)
        except (ValueError, TypeError):
            return jsonify({'error': 'selection_start and selection_end must be integers'}), 400
        
        # Optional fields
        parent_id_str = data.get('parent_id')
        parent_id = None
        if parent_id_str:
            try:
                parent_id = uuid.UUID(parent_id_str)
            except ValueError:
                return jsonify({'error': 'Invalid parent_id format'}), 400
        
        section = data.get('section')
        replace_with_link = data.get('replace_with_link', True)
        
        # Perform extraction
        result = ExtractionService.extract_selection(
            page_id=page_id,
            selection_start=selection_start,
            selection_end=selection_end,
            new_title=new_title,
            new_slug=new_slug,
            user_id=user_id,
            parent_id=parent_id,
            section=section,
            replace_with_link=replace_with_link
        )
        
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@extraction_bp.route('/pages/<uuid:page_id>/extract-heading', methods=['POST'])
@require_auth
@require_role(['writer', 'admin'])
def extract_heading_section(page_id):
    """
    Extract a heading section (heading + content until next heading) into a new page.
    
    Permissions: Writer, Admin
    """
    try:
        user_id = request.user_id
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        heading_text = data.get('heading_text')
        heading_level = data.get('heading_level')
        new_title = data.get('new_title')
        new_slug = data.get('new_slug')
        
        if not heading_text:
            return jsonify({'error': 'heading_text is required'}), 400
        if heading_level is None:
            return jsonify({'error': 'heading_level is required'}), 400
        if not new_title:
            return jsonify({'error': 'new_title is required'}), 400
        if not new_slug:
            return jsonify({'error': 'new_slug is required'}), 400
        
        # Validate heading_level
        try:
            heading_level = int(heading_level)
            if heading_level < 2 or heading_level > 6:
                return jsonify({'error': 'heading_level must be between 2 and 6'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'heading_level must be an integer'}), 400
        
        # Optional fields
        parent_id_str = data.get('parent_id')
        parent_id = None
        if parent_id_str:
            try:
                parent_id = uuid.UUID(parent_id_str)
            except ValueError:
                return jsonify({'error': 'Invalid parent_id format'}), 400
        
        section = data.get('section')
        promote_as = data.get('promote_as', 'child')
        
        if promote_as not in ['child', 'sibling']:
            return jsonify({'error': "promote_as must be 'child' or 'sibling'"}), 400
        
        # Perform extraction
        result = ExtractionService.extract_heading_section(
            page_id=page_id,
            heading_text=heading_text,
            heading_level=heading_level,
            new_title=new_title,
            new_slug=new_slug,
            user_id=user_id,
            parent_id=parent_id,
            section=section,
            promote_as=promote_as
        )
        
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@extraction_bp.route('/pages/<uuid:page_id>/promote-section', methods=['POST'])
@require_auth
@require_role(['writer', 'admin'])
def promote_section_from_toc(page_id):
    """
    Promote a section from TOC (by anchor) into a new page.
    
    Permissions: Writer, Admin
    """
    try:
        user_id = request.user_id
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        heading_anchor = data.get('heading_anchor')
        new_title = data.get('new_title')
        new_slug = data.get('new_slug')
        
        if not heading_anchor:
            return jsonify({'error': 'heading_anchor is required'}), 400
        if not new_title:
            return jsonify({'error': 'new_title is required'}), 400
        if not new_slug:
            return jsonify({'error': 'new_slug is required'}), 400
        
        # Optional fields
        promote_as = data.get('promote_as', 'child')
        section = data.get('section')
        
        if promote_as not in ['child', 'sibling']:
            return jsonify({'error': "promote_as must be 'child' or 'sibling'"}), 400
        
        # Perform extraction
        result = ExtractionService.promote_section_from_toc(
            page_id=page_id,
            heading_anchor=heading_anchor,
            new_title=new_title,
            new_slug=new_slug,
            user_id=user_id,
            promote_as=promote_as,
            section=section
        )
        
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

