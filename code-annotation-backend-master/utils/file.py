import os

from db.db_relation import RelationDB
from db.db_file import FileDB
from db.db_user import UserDB

from utils.path import *

user_db = UserDB()
file_db = FileDB()
relation_db = RelationDB()


def execute_read_file_data(rela_file_path: str, user_id: int):
    # === 1. 获取文件路径 ===
    file_path = path_file_open_file_abs(user_id, rela_file_path)
    if not os.path.exists(file_path):
        raise ValueError("文件不存在")

    # === 2. 读取文件内容 ===
    with open(file_path, "r") as f:
        file_content = f.read()

    # === 3. 读取文件标签 ===
    project_id = user_db.get_opened_project_id(user_id)
    if project_id is None:
        raise ValueError("用户没有打开项目")
    file_id = file_db.get_file_id_by_file_path(rela_file_path, project_id)
    if file_id is None:
        raise ValueError("文件在数据库中不存在")

    tag_data = relation_db.get_relations_by_file_id(file_id, project_id)
    # === 4. 返回文件内容和标签 ===
    return {"file_content": file_content, "tag_data": tag_data}


def reset_file_relations(file_id: int, tag_data: list[dict], project_id: int):
    relation_db.delete_relations_by_file_id(file_id, project_id)
    for tag_data_item in tag_data:
        relation_db.add_relation(
            start=tag_data_item["start"],
            end=tag_data_item["end"],
            arch_names=tag_data_item["arch_names"],
            project_id=project_id,
            file_id=file_id,
        )


def execute_save_file_data(user_id: int, rela_file_path: str, file_data: dict) -> bool:
    # === 1. 找到该文件对应的临时目录，保存内容到对应位置 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if not opened_project_id:
        print("用户没有打开项目")
        return False
    file_id = file_db.get_file_id_by_file_path(rela_file_path, opened_project_id)
    if not file_id:
        print("没有找到该文件")
        return False
    temp_file_dir = path_dir_tmp_file(user_id, file_id)
    if not os.path.exists(temp_file_dir):
        os.makedirs(temp_file_dir)

    tmp_count = file_db.get_file_tmp_count_by_id(file_id)
    if not file_db.update_file_tmp_count_by_id(file_id, tmp_count + 1):
        print("更新文件临时计数失败")
        return False
    tmp_file_name = str(tmp_count + 1) + ".tmp"
    file_content = file_data["file_content"]
    with open(os.path.join(temp_file_dir, tmp_file_name), "w") as f:
        f.write(file_content)
    # === 2. 保存到打开的对应文件里，并修改文件的修改时间 ===
    with open(
        path_file_open_file_abs(user_id=user_id, rela_file_path=rela_file_path), "w"
    ) as f:
        f.write(file_content)
    if not file_db.update_file_modify_time_by_id(file_id):
        print("更新文件修改时间失败")
        return False
    # === 3. 更新文件标签 ===

    reset_file_relations(file_id, file_data["tag_data"], opened_project_id)
    return True
