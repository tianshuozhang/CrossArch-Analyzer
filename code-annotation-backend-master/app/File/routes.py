from flask import request, jsonify, current_app
import os

from app.File import File
from db.db_file import FileDB
from db.db_user import UserDB
from utils.token import token_required

file_db = FileDB()
user_db = UserDB()


@File.route("/open", methods=["POST"])
@token_required
def open_file(user_id: int):
    # === 1. 获取要打开的文件路径 ===
    rela_file_path = request.form.get("file_path")
    if not rela_file_path:
        return (
            jsonify({"state": "fail", "description": "没有提供文件路径", "rst": {}}),
            404,
        )

    # === 2. 读取文件内容并返回 ===
    file_path = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "open", rela_file_path
    )
    if not os.path.exists(file_path):
        return jsonify({"state": "fail", "description": "文件不存在", "rst": {}}), 404

    with open(file_path, "r") as f:
        file_content = f.read()
        return (
            jsonify(
                {
                    "state": "success",
                    "description": "成功",
                    "rst": {"file_content": file_content},
                }
            ),
            200,
        )
    return jsonify({"state": "fail", "description": "读取文件内容失败", "rst": {}})


@File.route("/save", methods=["POST"])
@token_required
def save_file(user_id: int):
    # TODO:
    pass


@File.route("/cancel", methods=["POST"])
@token_required
def cancel_change_file(user_id: int):
    # TODO:
    pass
