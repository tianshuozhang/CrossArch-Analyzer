from flask import request, jsonify, current_app
import os, shutil, json
from datetime import datetime

from app.File import File
from db.db_file import FileDB
from db.db_user import UserDB
from db.db_relation import RelationDB
from utils.token import token_required
from utils.file import execute_read_file_data

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
                "rst": {
                    "file_content": file_data["file_content"],
                    "line_arch_tags": file_data["line_arch_tags"],
                },
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
    file_id = file_db.get_file_id_by_file_path(rela_file_path)
    if not file_id:
        return (
            jsonify({"state": "fail", "description": "没有找到该文件", "rst": {}}),
            404,
        )

    file_content = request.form.get("file_content")
    if not file_content:
        return (
            jsonify(
                {"state": "fail", "description": "没有提供要保存文件内容", "rst": {}}
            ),
            404,
        )
    # TODO:这里应该是不必要的
    file_tag = request.form.get("file_tag")
    if not file_tag:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有提供文件标签，如果当前没有文件标签，那么应该提供一个空的",
                    "rst": {},
                }
            ),
            404,
        )
    # === 2. 删除文件原来的relation，然后重新添加 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有打开项目，请先打开项目",
                    "rst": {},
                }
            ),
            404,
        )
    if not relation_db.delete_relations_by_file_id(file_id, opened_project_id):
        print("删除文件关系失败")
    for item in json.loads(file_tag):
        relation_db.add_relation(
            item["start"],
            item["end"],
            item["arch_names"],
            opened_project_id,
            file_id,
        )

    # === 2. 找到该文件对应的临时目录，保存内容到对应位置 ===
    temp_dir = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "tmp", str(file_id)
    )
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    tmp_count = file_db.get_file_tmp_count_by_id(file_id)
    if not file_db.update_file_tmp_count_by_id(file_id, tmp_count + 1):
        print("更新文件临时计数失败")
    tmp_file_name = str(tmp_count + 1) + ".tmp"
    with open(os.path.join(temp_dir, tmp_file_name), "w") as f:
        f.write(file_content)

    # === 3. 保存到打开的对应文件里，并修改文件的修改时间 ===
    file_path = os.path.join(
        current_app.config["ROOT"],
        "data",
        str(user_id),
        "open",
        "content",
        rela_file_path,
    )
    with open(file_path, "w") as f:
        f.write(file_content)
    if not file_db.update_file_modify_time_by_id(file_id):
        print("更新文件修改时间失败")

    # === 4. 返回成功 ===
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

    file_id = file_db.get_file_id_by_file_path(rela_file_path)
    if not file_id:
        return (
            jsonify({"state": "fail", "description": "没有找到该文件", "rst": {}}),
            404,
        )

    # === 2. 找到该文件对应的上一个临时文件路径 ===
    temp_dir = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "tmp", str(file_id)
    )
    tmp_file_name = file_db.get_file_tmp_count_by_id(file_id)
    tmp_file_path = os.path.join(temp_dir, str(tmp_file_name) + ".tmp")
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
    file_path = os.path.join(
        current_app.config["ROOT"],
        "data",
        str(user_id),
        "open",
        "content",
        rela_file_path,
    )
    with open(file_path, "w") as f:
        f.write(file_content)

    # === 5. 返回成功 ===
    return jsonify({"state": "success", "description": "成功", "rst": {}}), 200


@File.route("/close", methods=["POST"])
@token_required
def close_file(user_id: int):
    # === 1. 获取要关闭的文件路径，找到文件的ID ===
    rela_file_path = request.form.get("file_path")
    if not rela_file_path:
        return (
            jsonify({"state": "fail", "description": "没有提供文件路径", "rst": {}}),
            404,
        )

    file_id = file_db.get_file_id_by_file_path(rela_file_path)
    if not file_id:
        return (
            jsonify({"state": "fail", "description": "没有找到该文件", "rst": {}}),
            404,
        )

    # === 2. 删除该文件对应的临时文件目录，并且清零临时文件计数 ===
    temp_dir = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "tmp", str(file_id)
    )
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    if not file_db.update_file_tmp_count_by_id(file_id, 0):
        print("更新文件临时计数失败")

    # === 3. 返回成功 ===
    return jsonify({"state": "success", "description": "成功", "rst": {}}), 200
