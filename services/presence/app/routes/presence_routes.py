from app.routes import main
from flask import jsonify


@main.route("/api/presence/<user_id>", methods=["GET"])
def get_presence(user_id):
    # TODO: Implement presence retrieval
    return jsonify({"user_id": user_id, "status": "offline"}), 200


@main.route("/api/presence/<user_id>", methods=["POST"])
def update_presence(user_id):
    # TODO: Implement presence update
    return jsonify({"user_id": user_id, "status": "online"}), 200
