from flask import Blueprint, jsonify

wiki_bp = Blueprint('wiki', __name__)

@wiki_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'wiki'}), 200
