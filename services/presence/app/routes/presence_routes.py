from app.routes import main
from app.utils.health_check import get_health_status
from flask import jsonify


@main.route("/health", methods=["GET"])
def health():
    """Health check endpoint with process information"""
    health_status = get_health_status(
        service_name="presence",
        version="1.0.0",
        include_process_info=True,
    )
    return jsonify(health_status), 200


@main.route("/api/presence/<user_id>", methods=["GET"])
def get_presence(user_id):
    # TODO: Implement presence retrieval
    return jsonify({"user_id": user_id, "status": "offline"}), 200


@main.route("/api/presence/<user_id>", methods=["POST"])
def update_presence(user_id):
    # TODO: Implement presence update
    return jsonify({"user_id": user_id, "status": "online"}), 200
