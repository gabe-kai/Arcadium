from app.routes import main
from flask import jsonify


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
