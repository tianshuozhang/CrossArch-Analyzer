from flask import Blueprint, jsonify

ArchTag = Blueprint("ArchTag", __name__)

from app.ArchTag import routes
