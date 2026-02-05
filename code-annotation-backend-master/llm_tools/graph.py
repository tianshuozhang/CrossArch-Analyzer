from db.db_relation import RelationDB
from db.db_archTag import ArchTagDB
from db.db_user import UserDB
from db.db_file import FileDB

db_relation = RelationDB()
db_archTag = ArchTagDB()
db_user = UserDB()
db_file = FileDB()


def get_tag_data(user_id: int) -> dict | None:
    opened_project_id = db_user.get_opened_project_id(user_id)
    if opened_project_id is None:
        return None
    file_infos = db_file.get_files_by_project_id(opened_project_id)
    file_tag_data = {}
    for file_info in file_infos:
        file_tag_data[file_info["path"]] = db_relation.get_relations_by_file_id(
            file_info["id"]
        )
    return file_tag_data


def get_file_lines(user_id: int) -> dict | None:
    opened_project_id = db_user.get_opened_project_id(user_id)
    if opened_project_id is None:
        return None
    file_infos = db_file.get_files_by_project_id(opened_project_id)
    file_lines = {}
    for file_info in file_infos:
        file_path = file_info["path"]
        with open(file_path, "r") as f:
            file_lines[file_path] = len(f.readlines())
    return file_lines
