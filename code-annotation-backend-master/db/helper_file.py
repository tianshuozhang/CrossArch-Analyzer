import os
from app import app
from werkzeug.datastructures import FileStorage
import zipfile


def abs_path(file_path):
    return os.path.join(app.config["UPLOAD_ROOT"], file_path)


def load_file(file_path) -> str | None:
    """如果文件不存在，则返回None，否则返回文件内容"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return f.read()


def save_file(file_path, content) -> bool:
    """如果文件存在，则返回False，否则写入文件并返回True"""
    if os.path.exists(abs_path(file_path)):
        return False
    with open(abs_path(file_path), "w") as f:
        f.write(content)
        return True


def save_fileStorage(file_storage: FileStorage, file_path: str) -> bool:
    """如果文件存在，则返回False，否则写入文件并返回True"""
    if os.path.exists(abs_path(file_path)):
        return False
    file_storage.save(abs_path(file_path))
    return True


def get_metadata_from_zip(file_storage: FileStorage):
    """解析zip文件，用保存每个文件，返回<filepath, file_metadata>的元数据字典"""
    zip_buffer = file_storage.stream
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
        for zip_path in zip_ref.namelist():
            pass
