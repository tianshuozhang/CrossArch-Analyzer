import os, shutil
from flask import current_app

from db.db_project import ProjectDB
from db.db_file import FileDB
from db.db_modify import ModifyDB
from db.db_user import UserDB

from utils.dir import process_dir_structure

user_db = UserDB()
project_db = ProjectDB()
file_db = FileDB()
modiy_db = ModifyDB()


def execute_close_project(user_id: int, project_id: int, project_status: dict) -> bool:
    # === 1 根据项目的原状态设置项目的新状态，并压缩到指定位置 ===
    # === 1.1 如果项目状态是<open, processed, unmodified> ===
    if project_status == {
        "place": "open",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=0
        )
        shutil.make_archive(
            base_name=project_id,
            base_dir=os.path.join(current_app.config["ROOT"], user_id, "open"),
            root_dir=os.path.join(current_app.config["ROOT"], user_id, "project"),
            format="zip",
        )
    # === 1.2 如果项目状态是<open, processed, modified> ===
    elif project_status == {
        "place": "open",
        "processed": 1,
        "modified": 1,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=1
        )
        shutil.make_archive(
            base_name=project_id,
            base_dir=os.path.join(current_app.config["ROOT"], user_id, "open"),
            root_dir=os.path.join(current_app.config["ROOT"], user_id, "project"),
            format="zip",
        )

    # === 1.3 不存在其他情况 ===
    else:
        return False

    # === 2. 清理open目录，更新用户的open_project_id，并返回成功 ===
    open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
    shutil.rmtree(open_dir)
    os.makedirs(open_dir)
    try:
        process_dir_structure(open_dir)
    except:
        return False
    user_db.update_user_open_project_id(user_id, None)

    return True


def execute_save_tmp_project(user_id: int, project_id: int, project_status: dict):
    # === 1 根据项目的原状态设置项目的新状态，并压缩到指定位置 ===
    # === 1.1 如果项目状态是<tmp, processed, modified> ===
    if project_status == {
        "place": "tmp",
        "processed": 1,
        "modified": 1,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=1
        )
        shutil.make_archive(
            base_name=project_id,
            base_dir=os.path.join(current_app.config["ROOT"], user_id, "tmp"),
            root_dir=os.path.join(current_app.config["ROOT"], user_id, "project"),
            format="zip",
        )
    # === 1.2 不存在其他情况 ===
    else:
        return False

    # === 2. 清理tmp目录，更新用户的tmp_project_id，并返回成功 ===
    tmp_dir = os.path.join(current_app.config["ROOT"], user_id, "tmp")
    shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    try:
        process_dir_structure(tmp_dir)
    except Exception as e:
        return False
    user_db.update_user_tmp_project_id(user_id, None)
    return True


def before_open(project_id_to_open: int, user_id: int):
    user_opened_project_id = user_db.get_user_open_project_id(user_id)

    # === 1.如果要打开的项目和用户已打开的项目一样，直接返回 ===
    if user_opened_project_id is None or user_opened_project_id == project_id_to_open:
        return True

    # === 2.如果要打开的项目和用户已打开的项目不一样，需要关闭已打开的项目 ===
    opened_project_status = project_db.get_project_status(user_opened_project_id)
    if not execute_close_project(
        user_id, user_opened_project_id, opened_project_status
    ):
        return False

    # === 3.如果要打开的项目和用户临时保存的tmp项目不一样，需要保存tmp项目 ===
    user_tmp_project_id = user_db.get_user_tmp_project_id(user_id)
    if project_id_to_open != user_tmp_project_id:
        tmp_project_status = project_db.get_project_status(tmp_project_status)
        if not execute_save_tmp_project(
            user_id, user_tmp_project_id, tmp_project_status
        ):
            return False

    # === 4. 返回成功 ===
    return True


def before_unpack(project_id_to_modify: int, user_id: int, project_status: dict):
    # === 如果要修改的项目的状态是<save, unprocessed, unmodified>，那么需要检查用户之前是否有tmp项目，如果有那么就保存 ===
    if project_status == {
        "place": "save",
        "processed": 0,
        "modified": 0,
    }:
        user_tmp_project_id = user_db.get_user_tmp_project_id(user_id)
        if (
            user_tmp_project_id is not None
            and user_tmp_project_id != project_id_to_modify
        ):
            tmp_project_status = project_db.get_project_status(tmp_project_status)
            if not execute_save_tmp_project(
                user_id, user_tmp_project_id, tmp_project_status
            ):
                return False
    return True


def apply_modifies(project_root: str, project_id: int):
    pass


def register_project_files(project_root: str, project_id: int):
    # 对project_root下的所有文件进行注册
    for root, dirs, files in os.walk(project_root):
        for file in files:
            file_path = os.path.join(root, file)
            file_id = file_db.add_file(
                name=file,
                project_id=project_id,
                path=file_path,
            )


def _build_file_tree_with_path_list(file_paths: list[str]) -> list:
    """
    从路径列表递归构建目录树
    返回：[{name: "", type: "dir/file", children: []}]
    """
    tree = []
    for path in file_paths:
        parts = path.strip("/").split("/")
        current_level = tree
        for i, part in enumerate(parts):
            # 检查当前层级是否已存在该节点
            existing_node = next(
                (node for node in current_level if node["name"] == part), None
            )
            if not existing_node:
                # 创建新节点
                new_node = {
                    "name": part,
                    "type": "dir" if i < len(parts) - 1 else "file",
                    "children": [],
                }
                current_level.append(new_node)
                existing_node = new_node
            # 进入下一层级
            current_level = existing_node["children"]
    return tree


def get_file_tree_from_db(project_id: int) -> list:
    """
    从数据库递归构建目录树（仅未修改的文件）
    返回：[{name: "", type: "dir/file", children: []}]
    """
    files = file_db.get_files_by_project_id(project_id)
    modify_records = modiy_db.get_modify_records(project_id)
    file_paths = []
    for file in files:
        for record in modify_records:
            if file["id"] == record["file_id"]:
                file_paths.append(record["new_value"])
                break
        else:
            file_paths.append(file["path"])
    return _build_file_tree_with_path_list(file_paths)


def get_file_tree(root_dir: str) -> list:
    """
    递归构建目录树
    返回：[{name: "", type: "dir/file",id:file_id, children: []}]
    """
    tree = []
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        info = {
            "name": item,
            "type": "dir" if os.path.isdir(item_path) else "file",
            "id": file_db.get_file_id_by_file_path(item_path),
            "children": [],
        }
        if os.path.isdir(item_path):
            info["children"] = get_file_tree(item_path)
        tree.append(info)
    return tree
