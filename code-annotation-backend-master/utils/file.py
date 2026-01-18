from db.db_file import FileDB
from db.db_modify import ModifyDB

modify_db = ModifyDB()
file_db = FileDB()


def get_file_path_by_id(file_id: int):
    modify_records = modify_db.get_modify_records_by_file_id(file_id)
    file_path = None
    for modify_record in modify_records:
        if (
            modify_record["property_name"] == "path"
            and modify_record["operation_name"] == "mv"
        ):
            file_path = modify_record["new_value"]
            break
    if not file_path:
        file_path = file_db.get_file_path_by_id(file_id)
        if not file_path:
            return None

    return file_path
