from flask import request, jsonify
from werkzeug.datastructures import FileStorage
import os, shutil

from app.Project import Project
from db.db_project import ProjectDB
from db.db_user import UserDB
from db.db_file import FileDB
from utils.token import token_required
from utils.name import sanitize_project_name
from utils.project import (
    execute_open_project,
    register_project_files,
    make_file_tree_from_zip,
    save_file_tree_to_zip,
    execute_close_project,
    read_file_tree_from_zip,
)
from utils.path import *
from utils.zip import *

file_db = FileDB()
project_db = ProjectDB()
user_db = UserDB()


def _register_project_and_save(
    project_name: str, user_id: int, file: FileStorage, base_name, ext
):
    # === 1. 向数据库注册项目信息并保存项目 ===
    project_id = project_db.add_project(name=project_name, user_id=user_id)

    if ext == ".zip":
        # === 如果是zip，先解压整理好目录结构，然后压缩到对应位置 ===
        extract_root_path = path_dir_extract(user_id)
        path_tool_clean_dir(extract_root_path)
        zip_extract_fileStorage_to(file, path_dir_extract_content(user_id))
        os.makedirs(path_dir_extract_graph(user_id))
        zip_pack_dir_to(
            src_root_dir_path=extract_root_path,
            dst_zip_path=path_file_save_zip(user_id, project_id),
        )
        shutil.rmtree(extract_root_path)

    else:
        # === 如果不是zip，则生成一个整理好目录结构的zip ===
        zip_make_a_zip(
            path_file_save_zip(user_id, project_id),
            [
                (f"content/{file.filename}", file.stream.read()),
                ("graph/", ""),
            ],
        )

    # === 2. 向数据库注册文件信息 ===
    project_path = path_file_save_zip(user_id=user_id, project_id=project_id)
    register_project_files(project_path, project_id)

    # === 3. 获取项目的目录树并返回 ===
    project_tree = make_file_tree_from_zip(project_path)
    save_file_tree_to_zip(project_path, project_tree)
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
    project_list = project_db.get_project_view_list_by_user_id(user_id)
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
    project_tree = read_file_tree_from_zip(user_id=user_id, project_id=project_id)

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


@Project.route("/get_tree", methods=["GET"])
@token_required
def get_project_tree(user_id: int):
    # === 1. 读取项目ID ===
    project_id = request.args.get("project_id")
    if not project_id:
        return (
            jsonify({"state": "fail", "description": "请提供项目ID", "rst": {}}),
            400,
        )
    project_id = int(project_id)
    # === 2. 获取项目目录树 ===
    project_tree = read_file_tree_from_zip(user_id=user_id, project_id=project_id)
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
    project_zip_path = path_file_save_zip(user_id, project_id)
    if os.path.exists(project_zip_path):
        os.remove(project_zip_path)
    else:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "项目文件不存在",
                    "rst": {},
                }
            ),
            500,
        )

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
