from app.routes import main
from flask import jsonify, render_template


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
