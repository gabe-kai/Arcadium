from app.routes import main
from app.utils.health_check import get_health_status
from flask import jsonify


@main.route("/health", methods=["GET"])
def health():
    """Health check endpoint with process information"""
    health_status = get_health_status(
        service_name="chat",
        version="1.0.0",
        include_process_info=True,
    )
    return jsonify(health_status), 200


@main.route("/api/chat/channels", methods=["GET"])
def list_channels():
    # TODO: Implement channel listing
    return jsonify([]), 200


@main.route("/api/chat/channels/<channel_id>/messages", methods=["GET"])
def get_messages(channel_id):
    # TODO: Implement message retrieval
    return jsonify([]), 200


@main.route("/api/chat/channels/<channel_id>/messages", methods=["POST"])
def send_message(channel_id):
    # TODO: Implement message sending
    return jsonify({"id": "new", "status": "sent"}), 201
