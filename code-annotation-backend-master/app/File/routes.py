from flask import request, jsonify, current_app

import uuid, os

from app.File import File
from db.db_file import FileDB
from db.db_user import UserDB
from db.db_modify import ModifyDB
from utils.token import token_required
from utils.file import get_file_path_by_id

file_db = FileDB()
user_db = UserDB()
modify_db = ModifyDB()


@File.route("/add", methods=["POST"])
@token_required
def add_file(user_id: int):
    # === 1. 获取文件和参数 ===
    if "file" not in request.files:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400
    file_path = request.form.get("file_path")

    project_id = user_db.get_user_open_project_id(user_id)

    # === 2. 将文件保存到当前打开项目的uuid文件中，然后添加一条修改记录为从uuid路径到file_path ===
    file_ext = os.path.splitext(file.filename)[1]
    save_file_name = uuid.uuid4().hex + file_ext
    save_path = os.path.join(
        current_app.config["ROOT"], user_id, "project", project_id, save_file_name
    )
    file.save(save_path)
    file_id = file_db.add_file(save_file_name, project_id, save_path)
    modify_db.add_modify_record("mv", file_id, "path", file_path, project_id)

    # === 3. 返回文件id ===
    return (
        jsonify(
            {"state": "success", "description": "添加成功", "rst": {"file_id": file_id}}
        ),
        200,
    )


@File.route("/open", methods=["POST"])
@token_required
def open_file(user_id: int):
    # === 1. 获取要打开的文件id ===
    file_id = request.form.get("file_id")

    # === 2. 查询文件路径 ===
    file_path = get_file_path_by_id(file_id)
    if not file_path:
        return jsonify({"state": "fail", "description": "文件不存在", "rst": {}}), 404
    # === 3. 读取文件内容并返回 ===
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
    return jsonify({"state": "fail", "description": "文件不存在", "rst": {}})


@File.route("/modify", methods=["POST"])
@token_required
def modify_file(user_id: int):
    # === 1. 获取要修改的文件id和修改的内容 ===
    file_id = request.form.get("file_id")
    modify_content = request.form.get("modify_content")

    # === 2. 查询文件路径 ===
    file_path = get_file_path_by_id(file_id)
    if not file_path:
        return jsonify({"state": "fail", "description": "文件不存在", "rst": {}}), 404
    # === 3. 修改文件内容并返回 ===
    with open(file_path, "w") as f:
        f.write(modify_content)
        return jsonify({"state": "success", "description": "修改成功", "rst": {}}), 200
    return jsonify({"state": "fail", "description": "文件修改错误", "rst": {}}), 404
