from flask import request, jsonify, current_app
from werkzeug.datastructures import FileStorage
from typing import Union
import os, datetime, shutil, zipfile, json

from app.Project import Project
from db.db_project import ProjectDB
from db.db_user import UserDB
from db.db_modify import ModifyDB
from db.db_file import FileDB
from utils.token import token_required
from utils.name import sanitize_project_name
from utils.dir import process_dir_structure
from utils.project import (
    register_project_files,
    get_file_tree,
    get_file_tree_from_db,
    before_open,
    before_unpack,
    apply_modifies,
    execute_close_project,
)
from utils.modify import register_modify_data

file_db = FileDB()
project_db = ProjectDB()
user_db = UserDB()
modify_db = ModifyDB()


@Project.route("/upload", methods=["POST"])
@token_required
def upload_project(user_id: int):
    # === 1. 获取文件和参数 ===
    if "file" not in request.files:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400

    file: FileStorage = request.files["file"]
    if not file.filename:
        return jsonify({"state": "fail", "description": "请上传文件", "rst": {}}), 400
    base_name, ext = os.path.splitext(file.filename)
    project_name = sanitize_project_name(base_name)
    if not project_name:
        return (
            jsonify({"state": "fail", "description": "文件名无效", "rst": {}}),
            400,
        )

    # === 2. 向数据库注册项目信息 ===
    project_id = project_db.add_project(
        project_name, place="open", processed=1, modified=0, user_id=user_id
    )

    # === 3. 处理目录结构并保存到指定位置 ===
    open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
    try:
        process_dir_structure(open_dir)
    except Exception as e:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "处理open目录失败",
                    "rst": {"msg": str(e)},
                }
            ),
            500,
        )
    project_root = os.path.join(open_dir, "content")
    if ext == "zip":
        try:
            with zipfile.ZipFile(file.stream, "r") as zf:
                zf.testzip()
                zf.extractall(project_root)
        except zipfile.BadZipFile:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "上传的ZIP包无效",
                        "rst": {"msg": f"上传的ZIP包无效：{file.filename}"},
                    }
                ),
                400,
            )
        except PermissionError:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "处理open目录失败",
                        "rst": {"msg": f"无写入权限：{project_root}"},
                    }
                ),
                500,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "上传ZIP解压失败",
                        "rst": {"msg": f"上传ZIP解压失败：{str(e)}"},
                    }
                ),
                500,
            )
    else:
        file.save(os.path.join(project_root, file.filename))

    # === 4. 遍历项目文件注册文件信息 ===
    register_project_files(project_root, project_id)

    # === 5. 获取项目的目录树并返回 ===
    project_tree = get_file_tree(project_root)
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
        return jsonify({"state": "fail", "description": "空文件名", "rst": {}}), 400
    base_name, ext = os.path.splitext(file.filename)
    project_name = sanitize_project_name(base_name)
    if not project_name:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "文件名无效",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 向数据库注册项目信息，并将文件保存到指定位置 ===

    save_path = os.path.join(
        current_app.config["ROOT"], user_id, "project", f"{project_id}.zip"
    )
    # === 2.1 如果是zip文件 ===
    if ext == "zip":
        project_id = project_db.add_project(
            project_name, place="save", processed=0, modified=0, user_id=user_id
        )

        file.save(save_path)

    # === 2.2 如果是普通文件 ===
    else:
        project_id = project_db.add_project(
            project_name, place="save", processed=1, modified=0, user_id=user_id
        )
        file_content = file.stream.read()

        with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as zf:
            arcname = f"content/{file.filename}"
            zf.writestr(arcname, file_content)
            zf.writestr("graph/", "")

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


@Project.route("/open", methods=["POST"])
@token_required
def open_project(user_id: int):
    # === 1. 获取项目ID并读取项目的状态信息 ===
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
    project_status = project_db.get_project_status(project_id)

    # === 2. 处理before_open ===
    before_open(project_id_to_open=project_id, user_id=user_id)

    project_tree = None
    # === 2.1 如果项目状态是<save, unprocessed, unmodified> ===
    if project_status == {
        "place": "save",
        "processed": 0,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="open", processed=1, modified=0
        )
        open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
        process_dir_structure(open_dir)
        project_zip_path = os.path.join(
            current_app.config["ROOT"], user_id, "project", f"{project_id}.zip"
        )
        shutil.unpack_archive(project_zip_path, os.path.join(open_dir, "content"))
        register_project_files(os.path.join(open_dir, "content"), project_id)

    # === 2.2 如果项目状态是<tmp, processed, modified> ===
    elif project_status == {
        "place": "tmp",
        "processed": 1,
        "modified": 1,
    }:
        project_db.update_project_status(
            project_id, place="open", processed=1, modified=1
        )
        tmp_dir = os.path.join(current_app.config["ROOT"], user_id, "tmp")
        open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
        process_dir_structure(open_dir)
        shutil.copytree(tmp_dir, open_dir, dirs_exist_ok=True)

    # === 2.3 如果项目状态是<save, processed, unmodified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="open", processed=1, modified=0
        )
        save_dir = os.path.join(current_app.config["ROOT"], user_id, "project")
        open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
        shutil.unpack_archive(
            os.path.join(save_dir, f"{project_id}.zip"),
            os.path.join(open_dir),
        )

    # === 2.4 如果项目状态是<save, processed, modified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 1,
    }:
        project_db.update_project_status(
            project_id, place="open", processed=1, modified=1
        )
        save_dir = os.path.join(current_app.config["ROOT"], user_id, "project")
        open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
        shutil.unpack_archive(
            os.path.join(save_dir, f"{project_id}.zip"),
            os.path.join(open_dir),
        )
        project_dir = os.path.join(open_dir, "content")
        apply_modifies(project_dir, project_id)

    # === 2.5 如果项目状态是<open, processed, unmodified> ===
    elif project_status == {
        "place": "open",
        "processed": 1,
        "modified": 0,
    }:
        pass
    # === 2.6 如果项目状态是<open, processed, modified> ===
    elif project_status == {
        "place": "open",
        "processed": 1,
        "modified": 1,
    }:
        project_tree = get_file_tree_from_db(project_id)
    # === 2.7 不存在其他情况 ===
    else:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "项目状态无效",
                    "rst": {},
                }
            ),
            400,
        )

    # === 3. 更新用户的open_project_id，获取项目的目录树并返回 ===
    user_db.update_user_open_project_id(user_id, project_id)
    project_root = os.path.join(current_app.config["ROOT"], user_id, "open", "content")
    if not project_tree:
        project_tree = get_file_tree(project_root)
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
    open_project_id = user_db.get_user_open_project_id(user_id)
    if open_project_id is None:
        return (
            jsonify({"state": "fail", "description": "没有打开的项目", "rst": {}}),
            400,
        )
    project_status = project_db.get_project_status(open_project_id)

    # === 2. 执行关闭项目函数，关闭失败则返回失败 ===
    if not execute_close_project(user_id, open_project_id, project_status):
        return jsonify({"state": "fail", "description": "关闭项目失败", "rst": {}}), 400

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


@Project.route("/delete_file", methods=["POST"])
@token_required
def delete_file(user_id: int):
    # === 1. 获取要删除的文件id ===
    file_id = request.form.get("file_id")
    if not file_id:
        return jsonify({"state": "fail", "description": "缺少文件id", "rst": {}}), 400
    project_id = request.form.get("project_id")
    if not project_id:
        return jsonify({"state": "fail", "description": "缺少项目id", "rst": {}}), 400

    # === 2. 准备修改操作 ===
    modifiy_data_item = {
        "file_id": file_id,
        "property_name": "path",
        "operation_name": "delete",
        "new_value": "",
    }
    modify_data = [modifiy_data_item]
    # === 3. 注册修改数据 ===
    try:
        register_modify_data(project_id, modify_data)
    except Exception as e:
        return (
            jsonify({"state": "fail", "description": "注册修改数据失败", "rst": {}}),
            400,
        )

    # === 4. 返回成功 ===
    return (jsonify({"state": "success", "description": "成功", "rst": {}}), 200)


@Project.route("/rename_file", methods=["POST"])
@token_required
def rename_file(user_id: int):
    # === 1. 获取要重命名的文件id、修改的文件名 ===
    file_id = request.form.get("file_id")
    if not file_id:
        return jsonify({"state": "fail", "description": "缺少文件id", "rst": {}}), 400
    project_id = request.form.get("project_id")
    if not project_id:
        return jsonify({"state": "fail", "description": "缺少项目id", "rst": {}}), 400
    new_file_name = request.form.get("new_file_name")
    if not new_file_name:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "缺少修改的文件名",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 准备修改操作 ===
    old_path = file_db.get_file_path_by_id(file_id)
    new_path = os.path.join(os.path.dirname(old_path), new_file_name)
    modifiy_data_item = {
        "file_id": file_id,
        "property_name": "path",
        "operation_name": "mv",
        "new_value": new_path,
    }
    modify_data = [modifiy_data_item]
    # === 3. 注册修改数据 ===
    try:
        register_modify_data(project_id, modify_data)
    except Exception as e:
        return (
            jsonify({"state": "fail", "description": "注册修改数据失败", "rst": {}}),
            400,
        )

    # === 4. 返回成功 ===
    return (jsonify({"state": "success", "description": "成功", "rst": {}}), 200)


@Project.route("/move_file", methods=["POST"])
@token_required
def move_file(user_id: int):
    # === 1. 获取要移动的文件id、要移动到的目标位置 ===
    file_id = request.form.get("file_id")
    if not file_id:
        return jsonify({"state": "fail", "description": "缺少文件id", "rst": {}}), 400
    project_id = request.form.get("project_id")
    if not project_id:
        return jsonify({"state": "fail", "description": "缺少项目id", "rst": {}}), 400
    new_file_path = request.form.get("new_file_path")
    if not new_file_path:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "缺少目标位置",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 准备修改操作 ===
    modifiy_data_item = {
        "file_id": file_id,
        "property_name": "path",
        "operation_name": "mv",
        "new_value": new_file_path,
    }
    modify_data = [modifiy_data_item]
    # === 3. 注册修改数据 ===
    try:
        register_modify_data(project_id, modify_data)
    except Exception as e:
        return (
            jsonify({"state": "fail", "description": "注册修改数据失败", "rst": {}}),
            400,
        )

    # === 4. 返回成功 ===
    return (jsonify({"state": "success", "description": "成功", "rst": {}}), 200)


@Project.route("/modify", methods=["POST"])
@token_required
def modify_project(user_id: int):
    # === 1. 获取项目ID和修改内容，并查询项目状态 ===
    project_id = request.form.get("project_id")
    if not project_id:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "缺少项目id",
                    "rst": {},
                }
            ),
            400,
        )
    try:
        project_id = int(project_id)
    except ValueError:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "项目id格式错误",
                    "rst": {},
                }
            ),
            400,
        )

    modify_data = request.form.get("modifies")
    if not modify_data:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "缺少修改数据",
                    "rst": {},
                }
            ),
            400,
        )
    try:
        modify_data = json.loads(modify_data)
    except Exception:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "修改数据格式错误",
                    "rst": {},
                }
            ),
            400,
        )

    # === 2. 注册修改数据 ===
    try:
        register_modify_data(project_id, modify_data, user_id)
    except Exception:
        return (
            jsonify({"state": "fail", "description": "注册修改数据失败", "rst": {}}),
            400,
        )

    # === 3. 返回成功 ===
    return (
        jsonify(
            {
                "state": "success",
                "description": "修改成功",
                "rst": {},
            }
        ),
        200,
    )


@Project.route("/get-tree", methods=["GET"])
@token_required
def get_project_tree(user_id: int, project_id: int):
    # === 1. 读取项目的状态信息 ===
    project_status = project_db.get_project_status(project_id)
    if not project_status:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "没有该项目",
                    "rst": {"msg": f"项目ID是{project_id}"},
                }
            ),
            400,
        )

    # === 2.1 如果项目状态是<save, unprocessed, unmodified> ===
    if project_status == {
        "place": "save",
        "processed": 0,
        "modified": 0,
    }:
        if not project_db.update_project_status(
            project_id, place="tmp", processed=1, modified=0
        ):
            return (
                jsonify(
                    {"state": "fail", "description": "更新项目状态失败", "rst": {}}
                ),
                400,
            )
        if not before_unpack(project_id, user_id, project_status):
            return (
                jsonify(
                    {
                        "state": "fail",
                        "description": "before_unpack失败",
                        "rst": {},
                    }
                ),
                400,
            )
        user_db.update_user_tmp_project_id(user_id, project_id)
        tmp_dir = os.path.join(current_app.config["ROOT"], user_id, "tmp")
        process_dir_structure(tmp_dir)
        save_dir = os.path.join(current_app.config["ROOT"], user_id, "project")
        shutil.unpack_archive(
            os.path.join(save_dir, f"{project_id}.zip"),
            os.path.join(tmp_dir, "content"),
        )

        project_tree = get_file_tree(os.path.join(tmp_dir, "content"))

    # === 2.2 如果项目状态是<save, processed, unmodified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=0
        )
        project_tree = get_file_tree_from_db(project_id)

    # === 2.3 如果项目状态是<save, processed, modified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 1,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=1
        )
        project_tree = get_file_tree_from_db(project_id)

    # === 2.4 不存在其他情况 ===
    else:
        return (
            jsonify(
                {
                    "state": "fail",
                    "description": "项目状态错误",
                    "rst": {},
                }
            ),
            400,
        )

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
