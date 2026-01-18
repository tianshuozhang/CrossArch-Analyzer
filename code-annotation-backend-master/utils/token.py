from flask import request, jsonify, current_app
import jwt
from db.db_user import UserDB

user_db = UserDB()

# 受保护的 API（需要 Token）
from functools import wraps


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "请提供有效的 Token",
                        "rst": {},
                    }
                ),
                401,
            )
        SECRET_KEY = current_app.config["JWT_SECRET_KEY"]

        try:
            payload = jwt.decode(token[7:], SECRET_KEY, algorithms=["HS256"])
            user_id = payload["user_id"]
            # 验证用户是否仍存在（防账号删除后 Token 仍有效）
            if not user_db.get_user_by_id(user_id):
                return (
                    jsonify(
                        {
                            "state": "fail",
                            "description": "用户不存在",
                            "rst": {},
                        }
                    ),
                    401,
                )
        except jwt.ExpiredSignatureError:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "Token 已过期",
                        "rst": {},
                    }
                ),
                401,
            )
        except jwt.InvalidTokenError:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "无效的 Token",
                        "rst": {},
                    }
                ),
                401,
            )

        # 将 user_id 注入到视图函数中
        return f(user_id, *args, **kwargs)

    return decorated
