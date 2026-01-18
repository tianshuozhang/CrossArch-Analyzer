from flask import request, jsonify, current_app
from app.User import User

from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash, generate_password_hash
import jwt, os

from db.db_user import UserDB
from db.db_project import ProjectDB
from utils.token import token_required

user_db = UserDB()
project_db = ProjectDB()


def init_user_data(user_id: int):
    # === 检查用户的open、project、tmp目录是否存在，如果不存在则创建 ===
    try:
        user_dir = os.path.join(current_app.config["USER_DIR"], str(user_id))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        project_dir = os.path.join(user_dir, "project")
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        tmp_dir = os.path.join(user_dir, "tmp")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        open_dir = os.path.join(user_dir, "open")
        if not os.path.exists(open_dir):
            os.makedirs(open_dir)

    except Exception as e:
        raise e


@User.route("/login", methods=["POST"])
def login():
    # 获取请求参数
    data = request.form
    username = data.get("username")
    password = data.get("password")

    # 验证用户
    user = user_db.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "用户名或密码错误",
                    "rst": {},
                }
            ),
            400,
        )

    # 签发 JWT Token（有效期 7 天）
    SECRET_KEY = current_app.config["JWT_SECRET_KEY"]

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256",
    )
    try:
        init_user_data(user["id"])
    except Exception as e:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "初始化用户数据失败",
                    "rst": {"msg": str(e)},
                }
            ),
            500,
        )
    return (
        jsonify(
            {
                "state": "success",
                "description": "登录成功",
                "rst": {
                    "token": token,
                    "user_id": user["id"],
                    "username": user["username"],
                },
            }
        ),
        200,
    )


@User.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.form
        username = data.get("username")
        password = data.get("password")

        # 1. 参数校验
        if not username or not password:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "用户名或密码不能为空",
                        "rst": {},
                    }
                ),
                400,
            )

        if len(username) < 3 or len(username) > 50:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "用户名长度必须在3到50个字符之间",
                        "rst": {},
                    }
                ),
                400,
            )

        if len(password) < 6:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "密码长度至少6个字符",
                        "rst": {},
                    }
                ),
                400,
            )

        # 2. 检查用户名是否已存在
        if user_db.username_exists(username):
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "用户名已存在",
                        "rst": {},
                    }
                ),
                400,
            )

        # 3. 密码哈希（安全存储）
        password_hash = generate_password_hash(password)

        # 4. 插入数据库
        user_id = user_db.add_user(username, password_hash)

        # 5. 成功响应（不返回密码相关字段！）
        return (
            jsonify(
                {
                    "state": "success",
                    "description": "登录成功",
                    "rst": {"username": username, "user_id": user_id},
                }
            ),
            201,
        )  # 201 Created

    except Exception as e:
        print(f"Registration error: {e}")
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "服务器内部错误",
                    "rst": {},
                }
            ),
            500,
        )


@User.route("/api/modifyPassword", methods=["POST"])
@token_required
def change_password(user_id):
    """
    已登录用户修改密码
    请求头: Authorization: Bearer <token>
    请求体 (form-data):
        old_password: 当前密码
        new_password: 新密码（至少6位）
    """
    # === 1. 获取请求参数 ===
    data = request.form
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "旧密码或新密码不能为空",
                    "rst": {},
                }
            ),
            400,
        )

    if len(new_password) < 6:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "新密码长度至少6个字符",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 验证旧密码是否正确 ===
    user = user_db.get_user_by_id(user_id)
    if not user:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "用户不存在",
                    "rst": {},
                }
            ),
            404,
        )

    if not check_password_hash(user["password_hash"], old_password):
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "旧密码错误",
                    "rst": {},
                }
            ),
            400,
        )

    # === 3. 更新为新密码（哈希后）===
    new_password_hash = generate_password_hash(new_password)

    user_db.update_password(user_id, new_password_hash)

    return (
        jsonify(
            {
                "state": "success",
                "description": "密码修改成功",
                "rst": {},
            }
        ),
        200,
    )
