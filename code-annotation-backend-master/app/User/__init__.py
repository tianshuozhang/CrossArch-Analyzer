from flask import Blueprint, jsonify

User = Blueprint("User", __name__)

from app.User import routes

from db.db_user import UserDB

user_DB = UserDB()
