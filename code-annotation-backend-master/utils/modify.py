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
            raise NotImplementedError(f"不支持的操作，目前只支持mv和delete")
        for item in modify_records:
            file_id = item.get("file_id")
            property_name = item.get("property_name")
            if property_name == "path":
                orig_modify_records = modify_db.get_modify_records_by_file_id(file_id)
                if len(orig_modify_records) > 1:
                    raise ValueError("存在多个修改记录")
                if len(orig_modify_records) == 1:
                    orig_modify_record = orig_modify_records[0]
                    if orig_modify_record.get("operation_name") == "delete":
                        raise ValueError("尝试修改一个已删除的文件")
                    elif orig_modify_record.get("operation_name") == "mv":
                        orig_modify_record_id = orig_modify_record["id"]
                        modify_db.delete_modify_record_by_id(orig_modify_record_id)
                    else:
                        raise ValueError("存在未知的操作")
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
        if not _add_modify_record(modify_data):
            return False

    # === 2.2 如果项目状态是<save, processed, unmodified> ===
    elif project_status == {
        "place": "save",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="save", processed=1, modified=1
        )
        if not _add_modify_record(modify_data):
            return False

    # === 2.3 如果项目状态是<open, processed, unmodified> ===
    elif project_status == {
        "place": "open",
        "processed": 1,
        "modified": 0,
    }:
        project_db.update_project_status(
            project_id, place="open", processed=1, modified=1
        )
        if not _add_modify_record(modify_data):
            return False

    # === 2.4 不存在其他情况 ===
    else:
        return False

    return True
