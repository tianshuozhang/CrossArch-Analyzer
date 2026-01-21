from werkzeug.datastructures import FileStorage
from io import BytesIO
import zipfile, shutil


def zip_extract_fileStorage_to(src_file: FileStorage, dst_path: str):
    stream_data = src_file.stream.read()
    zip_buffer = BytesIO(stream_data)
    with zipfile.ZipFile(zip_buffer) as zipf:
        zipf.extractall(dst_path)


def zip_extract_file_to(src_zip_path: str, dst_dir_path: str):
    with zipfile.ZipFile(src_zip_path, "r") as zip_file:
        zip_file.extractall(dst_dir_path)


def zip_pack_dir_to(src_root_dir_path: str, dst_zip_path: str):
    if dst_zip_path.endswith(".zip"):
        dst_zip_path = dst_zip_path[:-4]
    shutil.make_archive(
        dst_zip_path,
        format="zip",
        root_dir=src_root_dir_path,
    )


def zip_make_a_zip(dst_zip_path: str, content: list[tuple[str, str | bytes]]):
    with zipfile.ZipFile(dst_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in content:
            path = item[0]
            file_content = item[1]
            zf.writestr(path, file_content)


def zip_read_namelist(zip_path: str):
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        namelist = zip_file.namelist()
        return namelist


def zip_add_to_zip(zip_path: str, content: list[tuple[str, str]]):
    with zipfile.ZipFile(zip_path, "a") as zip_file:
        for item in content:
            path = item[0]
            file_content = item[1]
            zip_file.writestr(path, file_content)


def zip_read_file_from_zip(zip_path: str, file_path: str):
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        return zip_file.read(file_path).decode("utf-8")
