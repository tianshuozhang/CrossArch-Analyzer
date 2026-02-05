from flask import Blueprint, jsonify

Project = Blueprint("Project", __name__)

from app.Project import routes
