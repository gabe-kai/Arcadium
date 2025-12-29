from app.routes import main
from flask import jsonify


@main.route("/api/assets", methods=["GET"])
def list_assets():
    # TODO: Implement asset listing
    return jsonify([]), 200


@main.route("/api/assets/<asset_id>", methods=["GET"])
def get_asset(asset_id):
    # TODO: Implement asset retrieval
    return jsonify({"id": asset_id}), 200


@main.route("/api/assets", methods=["POST"])
def upload_asset():
    # TODO: Implement asset upload
    return jsonify({"id": "new", "status": "uploaded"}), 201


@main.route("/api/assets/<asset_id>/download", methods=["GET"])
def download_asset(asset_id):
    # TODO: Implement asset download
    return jsonify({"message": "Download endpoint"}), 200
