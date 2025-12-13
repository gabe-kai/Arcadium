from flask import render_template, request, jsonify
from app.routes import main

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/pages', methods=['GET'])
def list_pages():
    # TODO: Implement page listing
    return jsonify([])

@main.route('/api/pages/<page_id>', methods=['GET'])
def get_page(page_id):
    # TODO: Implement page retrieval
    return jsonify({'id': page_id, 'content': ''})

@main.route('/api/pages', methods=['POST'])
def create_page():
    # TODO: Implement page creation
    return jsonify({'id': 'new', 'status': 'created'}), 201

