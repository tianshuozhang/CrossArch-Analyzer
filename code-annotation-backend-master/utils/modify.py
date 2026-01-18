import os, shutil
from flask import current_app

from db.db_user import UserDB
from db.db_modify import ModifyDB
from db.db_file import FileDB
from db.db_project import ProjectDB
from utils.project import before_unpack
from utils.dir import process_dir_structure

user_db = UserDB()
modify_db = ModifyDB()
file_db = FileDB()
project_db = ProjectDB()


def register_modify_data(project_id: int, modify_data: list[dict], user_id) -> bool:
    """注册修改数据"""

    def _add_modify_record(modify_records: list[dict]):
        if any(
            item.get("operation_name") not in ["delete", "mv"]
            for item in modify_records
        ):
            raise NotImplementedError(
                f"不支持{item.get('operation_name')}，目前只支持mv和delete"
            )
        for item in modify_records:
            file_id = item.get("file_id")
            property_name = item.get("property_name")
            if property_name == "path":
                old_path = file_db.get_file_path_by_id(file_id)
                new_path = item.get("new_value")
                if old_path.endswith("/"):
                    files_in_dir = file_db.get_files_with_path_prefix(
                        project_id, old_path
                    )
                    for f in files_in_dir:
                        modify_db.add_modify_record(
                            operation_name=item.get("operation_name"),
                            file_id=f["id"],
                            property_name="path",
                            new_value=new_path + f["path"][len(old_path) :],
                            project_id=project_id,
                        )
                else:
                    modify_db.add_modify_record(
                        operation_name=item.get("operation_name"),
                        file_id=file_id,
                        property_name="path",
                        new_value=new_path,
                        project_id=project_id,
                    )
            else:
                raise NotImplementedError(f"不支持的操作对象: {property_name}")

    # === 1. 处理before_unpack ===
    project_status = project_db.get_project_status(project_id)
    if not before_unpack(project_id, user_id, project_status):
        raise ValueError("不合法的项目状态")

    # === 2.1 如果项目状态是<save, unprocessed, unmodified> ===
    if project_status == {
        "place": "save",
        "processed": 0,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="tmp", processed=1, modified=1
        )
        tmp_dir = os.path.join(current_app.config["ROOT"], user_id, "tmp")
        process_dir_structure(tmp_dir)
        save_dir = os.path.join(current_app.config["ROOT"], user_id, "project")
        shutil.unpack_archive(
            os.path.join(save_dir, f"{project_id}.zip"),
            os.path.join(tmp_dir, "content"),
        )
        user_db.update_user_tmp_project_id(user_id, project_id)
        _add_modify_record(modify_data)

    # === 2.2 如果项目状态是<save, processed, unmodified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=1
        )
        _add_modify_record(modify_data)

    # === 2.3 如果项目状态是<open, processed, unmodified> ===
    elif project_status == {
        "place": "open",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="tmp", processed=1, modified=1
        )
        _add_modify_record(modify_data)

    # === 2.4 不存在其他情况 ===
    else:
        return False

    return True
