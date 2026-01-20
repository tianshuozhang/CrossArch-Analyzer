from flask import request, jsonify, current_app
from werkzeug.datastructures import FileStorage
from typing import Union
import os, datetime, shutil, zipfile, json
from io import BytesIO

from app.Project import Project
from db.db_project import ProjectDB
from db.db_user import UserDB
from db.db_file import FileDB
from utils.token import token_required
from utils.name import sanitize_project_name
from utils.project import (
    execute_open_project,
    register_project_files,
    get_file_tree,
    save_file_tree,
    execute_close_project,
)

file_db = FileDB()
project_db = ProjectDB()
user_db = UserDB()


def _get_project_tree(user_id: int, project_id: int):
    project_zip_path = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "project", f"{project_id}.zip"
    )
    with zipfile.ZipFile(project_zip_path, "r") as zip_file:
        project_tree = json.loads(zip_file.read("tree.json").decode("utf-8"))
    return project_tree


def _register_project_and_save(
    project_name: str, user_id: int, file: FileStorage, base_name, ext
):
    # === 1. 向数据库注册项目信息并保存项目 ===
    project_id = project_db.add_project(name=project_name, user_id=user_id)

    if ext == ".zip":
        extract_root_path = os.path.join(
            current_app.config["ROOT"], "data", str(user_id), "extract"
        )
        extract_content_path = os.path.join(extract_root_path, "content")
        if os.path.exists(extract_root_path):
            shutil.rmtree(extract_root_path)
        os.makedirs(extract_root_path)
        stream_data = file.stream.read()
        zip_buffer = BytesIO(stream_data)
        with zipfile.ZipFile(zip_buffer) as zipf:
            zipf.extractall(extract_content_path)
        graph_path = os.path.join(extract_root_path, "graph")
        os.makedirs(graph_path)
        project_path = os.path.join(
            current_app.config["ROOT"],
            "data",
            str(user_id),
            "project",
            f"{project_id}",
        )
        shutil.make_archive(project_path, format="zip", root_dir=extract_root_path)
        shutil.rmtree(extract_root_path)

    else:
        project_path = os.path.join(
            current_app.config["ROOT"],
            "data",
            str(user_id),
            "project",
            f"{project_id}.zip",
        )
        with zipfile.ZipFile(project_path, "w", zipfile.ZIP_DEFLATED) as zf:
            file_content = file.stream.read()
            arcname = f"{base_name}/{file.filename}"
            zf.writestr(arcname, file_content)
            zf.writestr("graph/", "")

    # === 2. 向数据库注册文件信息 ===
    project_path = os.path.join(
        current_app.config["ROOT"],
        "data",
        str(user_id),
        "project",
        f"{project_id}.zip",
    )
    register_project_files(project_path, project_id)

    # === 3. 获取项目的目录树并返回 ===
    project_tree = get_file_tree(project_path)
    save_file_tree(project_path, project_tree)
    # === 4. 返回项目ID和目录树 ===
    return project_id, project_tree


@Project.route("/upload", methods=["POST"])
@token_required
def upload_project(user_id: int):
    # === 1. 获取文件和参数 ===
    if "file" not in request.files:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400

    file: FileStorage = request.files["file"]
    if not file.filename:
        return (
            jsonify(
                {"state": "fail", "description": "请上传有文件名的文件", "rst": {}}
            ),
            400,
        )
    base_name, ext = os.path.splitext(file.filename)
    project_name = sanitize_project_name(base_name)
    if not project_name:
        return (
            jsonify({"state": "fail", "description": "文件名无效", "rst": {}}),
            400,
        )

    # === 2. 向数据库注册项目信息并保存项目 ===
    project_id, project_tree = _register_project_and_save(
        project_name=project_name,
        user_id=user_id,
        file=file,
        base_name=base_name,
        ext=ext,
    )

    # === 3. 打开该项目 ===
    try:
        execute_open_project(user_id=user_id, project_id=project_id)
    except Exception as e:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "上传项目时打开项目失败",
                    "rst": {"msg": f"打开项目失败：{str(e)}"},
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "state": "success",
                "description": "成功上传项目",
                "rst": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "file_tree": project_tree,
                },
            }
        )
    ), 201


@Project.route("/add", methods=["POST"])
@token_required
def add_project(user_id: int):
    # === 1. 获取文件和参数 ===
    if "file" not in request.files:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400

    file: FileStorage = request.files["file"]
    if not file.filename:
        return (
            jsonify(
                {"state": "fail", "description": "请上传有文件名的文件", "rst": {}}
            ),
            400,
        )
    base_name, ext = os.path.splitext(file.filename)
    project_name = sanitize_project_name(base_name)
    if not project_name:
        return (
            jsonify({"state": "fail", "description": "文件名无效", "rst": {}}),
            400,
        )

    # === 2. 向数据库注册项目信息，并将文件保存到指定位置 ===
    project_id, _ = _register_project_and_save(
        project_name=project_name,
        user_id=user_id,
        file=file,
        base_name=base_name,
        ext=ext,
    )

    return (
        jsonify(
            {
                "state": "success",
                "description": "成功添加项目",
                "rst": {
                    "project_id": project_id,
                    "project_name": project_name,
                },
            }
        )
    ), 201


@Project.route("/get_project_list", methods=["POST"])
@token_required
def get_project_list(user_id: int):
    # === 根据user_id获取用户已打开的项目列表 ===
    project_list = project_db.get_project_list_by_user_id(user_id)
    project_list = [
        {
            "id": project["id"],
            "name": project["name"],
            "modified_time": project["modified_time"],
        }
        for project in project_list
    ]
    return (
        jsonify(
            {
                "state": "success",
                "description": "成功获取项目列表",
                "rst": {"list": project_list},
            }
        ),
        200,
    )


@Project.route("/open", methods=["POST"])
@token_required
def open_project(user_id: int):
    # === 1. 获取项目ID ===
    project_id = request.form.get("project_id")
    if not project_id:
        return jsonify({"state": "fail", "description": "请提供项目ID", "rst": {}}), 400
    try:
        project_id = int(project_id)
    except ValueError:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "项目ID无效",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 打开该项目 ===
    try:
        execute_open_project(user_id=user_id, project_id=project_id)
    except Exception as e:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "打开项目失败",
                    "rst": {"msg": f"打开项目失败：{str(e)}"},
                }
            ),
            500,
        )

    # === 3. 获取项目的目录树 ===
    project_tree = _get_project_tree(user_id=user_id, project_id=project_id)

    # === 4. 返回结果 ===

    return (
        jsonify(
            {
                "state": "success",
                "description": "成功打开项目",
                "rst": {
                    "project_id": project_id,
                    "project_name": project_db.get_project_name(project_id),
                    "file_tree": project_tree,
                },
            }
        ),
        200,
    )


@Project.route("/close", methods=["POST"])
@token_required
def close_project(user_id: int):
    # === 1. 获取用户当前打开的项目ID、状态、名字 ===
    open_project_id = user_db.get_opened_project_id(user_id)
    if open_project_id is None:
        return (
            jsonify({"state": "fail", "description": "没有打开的项目", "rst": {}}),
            400,
        )

    # === 2. 执行关闭项目函数 ===
    execute_close_project(user_id, open_project_id)

    # === 3. 返回成功 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "关闭项目成功",
                "rst": {},
            }
        ),
        200,
    )


@Project.route("/get-tree", methods=["GET"])
@token_required
def get_project_tree(user_id: int):
    # === 1. 读取项目ID ===
    project_id = request.args.get("project_id")

    # === 2. 获取项目目录树 ===
    project_tree = _get_project_tree(user_id=user_id, project_id=project_id)
    # === 3. 返回目录树 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "成功获取项目目录树",
                "rst": {
                    "project_id": project_id,
                    "project_name": project_db.get_project_name(project_id),
                    "file_tree": project_tree,
                },
            }
        ),
        200,
    )


@Project.route("/delete", methods=["POST"])
@token_required
def delete_project(user_id: int):
    # === 1. 获取项目ID ===
    project_id = request.form.get("project_id")
    project_id = int(project_id)

    # === 2. 如果该项目是当前打开的项目，那么先关闭项目 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if opened_project_id == project_id:
        execute_close_project(user_id, opened_project_id)

    # === 3. 删除项目 ===
    if not project_db.delete_project_by_id(project_id):
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "删除项目失败",
                    "rst": {},
                }
            ),
            500,
        )
    project_zip_path = os.path.join(
        current_app.config["ROOT"], "data", str(user_id), "project", f"{project_id}.zip"
    )
    if os.path.exists(project_zip_path):
        os.remove(project_zip_path)

    # === 4. 返回成功 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "成功删除项目",
                "rst": {},
            }
        ),
        200,
    )
