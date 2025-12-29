from flask import Blueprint

main = Blueprint("main", __name__)

from app.routes import asset_routes  # noqa: E402,F401
