from app.routes import main
from app.utils.health_check import get_health_status
from flask import jsonify, render_template


@main.route("/health", methods=["GET"])
def health():
    """Health check endpoint with process information"""
    health_status = get_health_status(
        service_name="admin",
        version="1.0.0",
        include_process_info=True,
    )
    return jsonify(health_status), 200


@main.route("/")
def dashboard():
    # TODO: Implement admin dashboard
    return render_template("dashboard.html")


@main.route("/api/admin/stats", methods=["GET"])
def get_stats():
    # TODO: Implement stats retrieval
    return jsonify({}), 200


@main.route("/api/admin/users", methods=["GET"])
def list_users():
    # TODO: Implement user listing
    return jsonify([]), 200
