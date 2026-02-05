from flask import request, jsonify
import os, shutil, json

from app.File import File
from db.db_file import FileDB
from db.db_user import UserDB
from db.db_relation import RelationDB
from utils.token import token_required
from utils.file import execute_read_file_data, execute_save_file_data
from utils.path import *

file_db = FileDB()
user_db = UserDB()
relation_db = RelationDB()


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

    # === 2. 读取文件数据并返回 ===
    try:
        file_data = execute_read_file_data(rela_file_path, user_id)
    except:
        return jsonify({"state": "fail", "description": "读取文件内容失败", "rst": {}})
    return (
        jsonify(
            {
                "state": "success",
                "description": "成功",
                "rst": {"file_data": file_data},
            }
        ),
        200,
    )


@File.route("/save", methods=["POST"])
@token_required
def save_file(user_id: int):
    # === 1. 获取要保存的文件路径，找到文件的ID，获取文件数据 ===
    rela_file_path = request.form.get("file_path")
    if not rela_file_path:
        return (
            jsonify({"state": "fail", "description": "没有提供文件路径", "rst": {}}),
            404,
        )
    file_data = request.form.get("file_data")
    if not file_data:
        return (
            jsonify(
                {"state": "fail", "description": "没有提供要保存文件内容", "rst": {}}
            ),
            404,
        )
    # === 2. 执行保存文件 ===
    if not execute_save_file_data(user_id, rela_file_path, file_data):
        return jsonify({"state": "fail", "description": "保存文件内容失败", "rst": {}})
    # === 3. 返回成功 ===
    return jsonify({"state": "success", "description": "成功", "rst": {}}), 200


@File.route("/cancel", methods=["POST"])
@token_required
def cancel_change_file(user_id: int):
    # === 1. 获取要取消的文件路径，找到文件的ID ===
    rela_file_path = request.form.get("file_path")
    if not rela_file_path:
        return (
            jsonify({"state": "fail", "description": "没有提供文件路径", "rst": {}}),
            404,
        )
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        print("用户没有打开项目")
        return (
            jsonify({"state": "fail", "description": "用户没有打开项目", "rst": {}}),
            404,
        )
    file_id = file_db.get_file_id_by_file_path(rela_file_path, opened_project_id)
    if not file_id:
        return (
            jsonify({"state": "fail", "description": "没有找到该文件", "rst": {}}),
            404,
        )

    # === 2. 找到该文件对应的上一个临时文件路径 ===
    tmp_file_name = file_db.get_file_tmp_count_by_id(file_id)
    tmp_file_path = os.path.join(
        path_dir_tmp_file(user_id, file_id), str(tmp_file_name) + ".tmp"
    )
    if not os.path.exists(tmp_file_path):
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有找到该文件对应的临时文件",
                    "rst": {},
                }
            ),
            404,
        )

    # === 3. 读出临时文件里的内容，删除临时文件，减少临时文件计数 ===
    with open(tmp_file_path, "r") as f:
        file_content = f.read()
    os.remove(tmp_file_path)
    if not file_db.update_file_tmp_count_by_id(file_id, tmp_file_name - 1):
        print("更新文件临时计数失败")

    # === 4. 将内容写入打开的文件里
    with open(path_file_open_file_abs(user_id, rela_file_path), "w") as f:
        f.write(file_content)

    # === 5. 返回成功 ===
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


@File.route("/close", methods=["POST"])
@token_required
def close_file(user_id: int):
    # === 1. 解析前端参数file_path, file_data ===
    rela_file_path = request.form.get("file_path")
    if not rela_file_path:
        return (
            jsonify({"state": "fail", "description": "没有提供文件路径", "rst": {}}),
            404,
        )
    file_data = request.form.get("file_data")
    if not file_data:
        return (
            jsonify(
                {"state": "fail", "description": "没有提供要保存文件内容", "rst": {}}
            ),
            404,
        )
    # === 2. 执行保存文件 ===
    if not execute_save_file_data(user_id, rela_file_path, file_data):
        return jsonify({"state": "fail", "description": "保存文件内容失败", "rst": {}})

    # === 3. 删除该文件对应的临时文件目录，并且清零临时文件计数 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    file_id = file_db.get_file_id_by_file_path(rela_file_path, opened_project_id)
    if not file_id:
        return (
            jsonify({"state": "fail", "description": "没有找到该文件", "rst": {}}),
            404,
        )
    temp_file_dir = path_dir_tmp_file(user_id, file_id)
    if os.path.exists(temp_file_dir):
        shutil.rmtree(temp_file_dir)

    if not file_db.update_file_tmp_count_by_id(file_id, 0):
        print("更新文件临时计数失败")

    # === 3. 返回成功 ===
    return jsonify({"state": "success", "description": "成功", "rst": {}}), 200
