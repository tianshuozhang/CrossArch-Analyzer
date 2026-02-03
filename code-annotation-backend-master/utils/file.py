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
    # 前端可能传入 'content/xxx' 或 'xxx'，后端打开目录为 .../open/content/
    # 为避免出现 .../open/content/content/xxx 的重复目录，需要适当处理路径
    fs_rel_path = rela_file_path
    if isinstance(fs_rel_path, str) and fs_rel_path.startswith("content/"):
        fs_rel_path = fs_rel_path[len("content/") :]
    file_path = path_file_open_file_abs(user_id, fs_rel_path)
    
    # 如果文件不存在，尝试原始路径（可能前端传入的路径没有content/前缀）
    if not os.path.exists(file_path):
        file_path = path_file_open_file_abs(user_id, rela_file_path)
        if not os.path.exists(file_path):
            raise ValueError(f"文件不存在: {file_path}")

    # === 2. 读取文件内容 ===
    with open(file_path, "r") as f:
        file_content = f.read()

    # === 3. 读取文件标签 ===
    project_id = user_db.get_opened_project_id(user_id)
    if project_id is None:
        raise ValueError("用户没有打开项目")
    # 数据库中记录的路径可能包含 'content/' 前缀，需要尝试多种查询方式
    print(f"DEBUG: 尝试查询数据库路径: '{rela_file_path}' in project {project_id}")
    file_id = file_db.get_file_id_by_file_path(rela_file_path, project_id)
    print(f"DEBUG: 第一次查询结果: file_id = {file_id}")
    
    # 如果找不到，尝试添加content/前缀的路径
    if file_id is None:
        alt_path = "content/" + rela_file_path
        print(f"DEBUG: 尝试查询替代路径: '{alt_path}' in project {project_id}")
        file_id = file_db.get_file_id_by_file_path(alt_path, project_id)
        print(f"DEBUG: 添加前缀后查询结果: file_id = {file_id}")
    
    # 如果还是找不到，尝试去掉content/前缀的路径
    if file_id is None and rela_file_path.startswith("content/"):
        alt_path2 = rela_file_path[len("content/"):]
        print(f"DEBUG: 尝试查询去掉前缀路径: '{alt_path2}' in project {project_id}")
        file_id = file_db.get_file_id_by_file_path(alt_path2, project_id)
        print(f"DEBUG: 去掉前缀后查询结果: file_id = {file_id}")
    # 再次检查，如果还是没找到，尝试相反的逻辑
    if file_id is None:
        if rela_file_path.startswith("content/"):
            # 如果原始路径有content/前缀，尝试不带前缀的
            alt_path3 = rela_file_path[len("content/"):]
            print(f"DEBUG: 尝试查询不带前缀路径: '{alt_path3}' in project {project_id}")
            file_id = file_db.get_file_id_by_file_path(alt_path3, project_id)
        else:
            # 如果原始路径没有content/前缀，尝试添加前缀
            alt_path4 = "content/" + rela_file_path
            print(f"DEBUG: 尝试查询带前缀路径: '{alt_path4}' in project {project_id}")
            file_id = file_db.get_file_id_by_file_path(alt_path4, project_id)
    if file_id is None:
        print(f"DEBUG: 所有路径查询都失败，文件路径: '{rela_file_path}', 项目ID: {project_id}")
        # 调试：列出项目中所有文件路径
        all_files = file_db.get_files_by_project_id(project_id)
        print(f"DEBUG: 项目 {project_id} 中的文件数量: {len(all_files)}")
        for f in all_files[:10]:  # 只打印前10个
            print(f"DEBUG: 项目文件: {f['path']}")
        raise ValueError(f"文件在数据库中不存在: {rela_file_path}")

    tag_data = relation_db.get_relations_by_file_id(file_id, project_id)
    print(f"DEBUG: 成功找到文件，内容长度: {len(file_content)}, 标签数量: {len(tag_data) if tag_data else 0}")
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
    # 如果找不到，尝试添加content/前缀的路径
    if not file_id:
        file_id = file_db.get_file_id_by_file_path("content/" + rela_file_path, opened_project_id)
    # 如果还是找不到，尝试去掉content/前缀的路径
    if not file_id and rela_file_path.startswith("content/"):
        file_id = file_db.get_file_id_by_file_path(rela_file_path[len("content/"):], opened_project_id)
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
