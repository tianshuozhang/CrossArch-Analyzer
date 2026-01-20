import os
from flask import current_app

from db.db_relation import RelationDB
from db.db_file import FileDB
from db.db_user import UserDB

user_db = UserDB()
file_db = FileDB()
relation_db = RelationDB()


def execute_read_file_data(rela_file_path: str, user_id: int):
    # === 1. 获取文件路径 ===
    file_path = os.path.join(
        current_app.config["ROOT"],
        "data",
        str(user_id),
        "open",
        "content",
        rela_file_path,
    )
    if not os.path.exists(file_path):
        raise ValueError("文件不存在")

    # === 2. 读取文件内容 ===
    with open(file_path, "r") as f:
        file_content = f.read()

    # === 3. 读取文件标签 ===
    project_id = user_db.get_opened_project_id(user_id)
    if project_id is None:
        raise ValueError("用户没有打开项目")
    file_id = file_db.get_file_id_by_file_path(rela_file_path)
    if file_id is None:
        raise ValueError("文件在数据库中不存在")

    relations = relation_db.get_relations_by_file_id(file_id, project_id)
    line_arch_tags = []
    for relation in relations:
        start, end = relation["start"], relation["end"]
        try:
            start, end = int(start), int(end)
        except:
            raise ValueError("关系数据格式错误")

        for line in range(start, end + 1):
            line_arch_tags.append(
                {
                    "line": line,
                    "tags": relation["arch_names"],
                }
            )

    # === 4. 返回文件内容和标签 ===
    return {"file_content": file_content, "line_arch_tags": line_arch_tags}
