from flask import Blueprint

main = Blueprint('main', __name__)

from app.routes import chat_routes

