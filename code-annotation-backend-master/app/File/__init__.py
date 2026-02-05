from flask import Blueprint, jsonify

File = Blueprint("File", __name__)

from app.File import routes
