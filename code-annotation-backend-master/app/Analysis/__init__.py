from flask import Blueprint

Analysis = Blueprint("Analysis", __name__)

from app.Analysis import routes