from flask import request, jsonify, current_app
from app.User import User

from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash, generate_password_hash
import jwt, os, shutil

from db.db_user import UserDB
from db.db_project import ProjectDB
from db.db_archTag import ArchTagDB
from utils.token import token_required
from utils.path import *

user_db = UserDB()
project_db = ProjectDB()
arch_tag_db = ArchTagDB()


def init_user_data(user_id: int):
    # 创建用户目录
    user_dir = path_dir_user(user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # 创建用户的项目目录和open目录
    save_dir = path_dir_save(user_id)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    open_dir = path_dir_open(user_id)
    if os.path.exists(open_dir):
        print("WARNING:用户有之前没有清理的打开项目")
        path_tool_clean_dir(open_dir)
        if not user_db.update_opened_project_id(user_id, 0):
            print("ERROR:更新用户已打开项目失败")
    else:
        os.makedirs(open_dir)
    # 创建用户默认标签
    arch_tag_db.set_default_arch_tags(user_id)


@User.route("/login", methods=["POST"])
def login():
    # 获取请求参数
    data = request.form
    username = data.get("username")
    password = data.get("password")
    print(f"Login attempt: {username}")
    print(f"Password received: {password}")
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
    init_user_data(user["id"])

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


@User.route("/register", methods=["POST"])
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
                    "description": "服务器异常",
                    "rst": {},
                }
            ),
            500,
        )


@User.route("/modify_password", methods=["POST"])
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

    # === 2. 验证密码是否正确 ===

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

    if old_password == new_password:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "新密码不能与旧密码相同",
                    "rst": {},
                }
            ),
            400,
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

    if not user_db.update_password(user_id, new_password_hash):
        print(f"后端数据库里密码修改失败, {user_id=}, {new_password_hash=}")
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "后端数据库里密码修改失败",
                    "rst": {},
                }
            ),
            500,
        )

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
