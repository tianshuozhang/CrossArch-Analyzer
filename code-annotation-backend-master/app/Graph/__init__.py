from flask import Blueprint, jsonify

Graph = Blueprint("Graph", __name__)

from app.File import routes
