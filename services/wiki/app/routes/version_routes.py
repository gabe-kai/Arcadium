"""Version history endpoints"""
import uuid
from flask import Blueprint, request, jsonify
from app import db
from app.models.page import Page
from app.models.page_version import PageVersion
from app.middleware.auth import optional_auth, require_auth, require_role
from app.services.version_service import VersionService
from app.utils.markdown_service import markdown_to_html

version_bp = Blueprint('versions', __name__)


@version_bp.route('/pages/<uuid:page_id>/versions', methods=['GET'])
@optional_auth
def get_version_history(page_id):
    """
    Get version history for a page.
    
    Permissions: Public (viewer)
    """
    try:
        # Check if page exists
        page = db.session.get(Page, page_id)
        if not page:
            return jsonify({'error': 'Page not found'}), 404
        
        # Get all versions
        versions = VersionService.get_all_versions(page_id)
        
        # Format response
        version_list = []
        for version in versions:
            version_dict = {
                'version': version.version,
                'title': version.title,
                'changed_by': {
                    'id': str(version.changed_by),
                    'username': 'user'  # Placeholder - would come from auth service
                },
                'change_summary': version.change_summary,
                'created_at': version.created_at.isoformat() if version.created_at else None
            }
            
            # Add diff stats if available
            if version.diff_data:
                version_dict['diff_stats'] = {
                    'added_lines': version.diff_data.get('added_lines', 0),
                    'removed_lines': version.diff_data.get('removed_lines', 0),
                    'char_diff': version.diff_data.get('char_diff', 0)
                }
            else:
                version_dict['diff_stats'] = {
                    'added_lines': 0,
                    'removed_lines': 0,
                    'char_diff': 0
                }
            
            version_list.append(version_dict)
        
        return jsonify({'versions': version_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/pages/<uuid:page_id>/versions/<int:version>', methods=['GET'])
@optional_auth
def get_version(page_id, version):
    """
    Get a specific version of a page.
    
    Permissions: Public (viewer)
    """
    try:
        # Check if page exists
        page = db.session.get(Page, page_id)
        if not page:
            return jsonify({'error': 'Page not found'}), 404
        
        # Get version
        version_obj = VersionService.get_version(page_id, version)
        if not version_obj:
            return jsonify({'error': f'Version {version} not found'}), 404
        
        # Convert to dict and add HTML content
        version_dict = version_obj.to_dict()
        version_dict['html_content'] = markdown_to_html(version_obj.content)
        
        # Format changed_by
        version_dict['changed_by'] = {
            'id': str(version_obj.changed_by),
            'username': 'user'  # Placeholder - would come from auth service
        }
        
        return jsonify(version_dict), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/pages/<uuid:page_id>/versions/compare', methods=['GET'])
@optional_auth
def compare_versions(page_id):
    """
    Compare two versions of a page.
    
    Query Parameters:
    - from (required): First version number
    - to (required): Second version number
    
    Permissions: Public (viewer)
    """
    try:
        # Check if page exists
        page = db.session.get(Page, page_id)
        if not page:
            return jsonify({'error': 'Page not found'}), 404
        
        # Get query parameters
        from_version = request.args.get('from')
        to_version = request.args.get('to')
        
        if not from_version or not to_version:
            return jsonify({'error': 'Query parameters "from" and "to" are required'}), 400
        
        try:
            from_version = int(from_version)
            to_version = int(to_version)
        except ValueError:
            return jsonify({'error': 'Version numbers must be integers'}), 400
        
        # Compare versions
        comparison = VersionService.compare_versions(page_id, from_version, to_version)
        
        # Format response
        response_data = {
            'from_version': from_version,
            'to_version': to_version,
            'version1': {
                'version': comparison['version1']['version'],
                'title': comparison['version1']['title'],
                'changed_by': {
                    'id': comparison['version1']['changed_by'],
                    'username': 'user'  # Placeholder
                },
                'created_at': comparison['version1']['created_at']
            },
            'version2': {
                'version': comparison['version2']['version'],
                'title': comparison['version2']['title'],
                'changed_by': {
                    'id': comparison['version2']['changed_by'],
                    'username': 'user'  # Placeholder
                },
                'created_at': comparison['version2']['created_at']
            },
            'diff': comparison['diff']
        }
        
        return jsonify(response_data), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/pages/<uuid:page_id>/versions/<int:version>/restore', methods=['POST'])
@require_auth
@require_role(['writer', 'admin'])
def restore_version(page_id, version):
    """
    Restore a page to a specific version.
    
    Permissions: Writer (own pages) or Admin (any page)
    """
    try:
        # Get user info from request
        user_id = request.user_id
        user_role = request.user_role
        
        # Check if page exists
        page = db.session.get(Page, page_id)
        if not page:
            return jsonify({'error': 'Page not found'}), 404
        
        # Check permissions
        if user_role == 'writer' and page.created_by != user_id:
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'Writers can only restore pages they created'
            }), 403
        
        # Restore version
        restored_page = VersionService.rollback_to_version(
            page_id=page_id,
            version=version,
            user_id=user_id,
            user_role=user_role
        )
        
        # Get the new version number (should be the latest)
        latest_version = VersionService.get_latest_version(page_id)
        new_version = latest_version.version if latest_version else version
        
        return jsonify({
            'message': 'Version restored successfully',
            'new_version': new_version,
            'page': {
                'id': str(restored_page.id),
                'title': restored_page.title,
                'version': restored_page.version
            }
        }), 200
    
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

