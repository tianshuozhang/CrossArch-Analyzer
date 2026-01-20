import os, shutil, zipfile
from flask import current_app

from db.db_project import ProjectDB
from db.db_file import FileDB
from db.db_user import UserDB

user_db = UserDB()
project_db = ProjectDB()
file_db = FileDB()


def execute_close_project(user_id: int, project_id: int):
    # === 1. 把项目保存到指定位置 ===
    target_project_path = os.path.join(
        current_app.config["ROOT"], "data", user_id, "project", f"{project_id}"
    )
    open_project_path = os.path.join(current_app.config["ROOT"], user_id, "open")
    shutil.make_archive(
        base_name=target_project_path,
        root_dir=open_project_path,
        format="zip",
    )
    # === 2. 清理open目录，更新用户的open_project_id，并返回成功 ===
    open_dir = os.path.join(current_app.config["ROOT"], user_id, "open")
    shutil.rmtree(open_dir)
    os.makedirs(open_dir)
    if not user_db.update_opened_project_id(user_id, 0):
        print("ERROR:更新用户已打开项目失败")


def prepare_open_dir(user_id: int):
    open_dir = os.path.join(current_app.config["ROOT"], "data", user_id, "open")
    try:
        shutil.rmtree(open_dir)
        os.makedirs(os.path.join(open_dir, "content"))
        os.makedirs(os.path.join(open_dir, "graph"))
    except Exception as e:
        print(f"后端错误：准备open失败， {e.args}")


def execute_open_project(user_id: int, project_id: int):
    # === 1. 检查用户是否有已打开的项目，如果有，那么关闭它 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if opened_project_id is not None and opened_project_id != 0:
        execute_close_project(user_id, project_id)

    # === 2. 如果用户已打开的和要打开的项目一样，那么直接返回 ===
    if opened_project_id == project_id:
        return True

    # === 3. 打开项目 ===
    save_project_path = os.path.join(
        current_app.config["ROOT"], "data", user_id, "project", f"{project_id}.zip"
    )
    project_processed = project_db.get_project_processed(project_id)
    if project_processed is None:
        raise ValueError("项目不存在")
    if project_processed:
        target_project_path = os.path.join(
            current_app.config["ROOT"], "data", user_id, "open"
        )
    else:
        target_project_path = os.path.join(
            current_app.config["ROOT"], "data", user_id, "open", "content"
        )
        if os.path.exists(target_project_path):
            raise ValueError("用户的open目录没有清理干净")
        prepare_open_dir(user_id)
        project_db.update_project_processed(project_id, 1)

    shutil.unpack_archive(save_project_path, target_project_path)
    # === 4. 更新用户已打开项目 ===
    if not user_db.update_opened_project_id(user_id, project_id):
        raise ValueError("更新用户已打开项目失败")


def register_project_files(zip_path: str, project_id: int):
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        namelist = zip_file.namelist()
        for name in namelist:
            file_id = file_db.add_file(
                name=name,
                project_id=project_id,
                path=os.path.join(zip_path, name),
            )


def get_file_tree(zip_path: str) -> list:
    """
    递归构建目录树
    返回：[{name: "", type: "dir/file", children: []}]
    """
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        namelist = zip_file.namelist()

    # 构建虚拟文件系统（扁平路径 → 嵌套结构）
    root = {}

    for name in namelist:
        # 忽略空项
        if not name.strip():
            continue

        # ZIP 中目录以 '/' 结尾，但有些工具不显式包含目录条目
        # 我们通过路径分割自动推断目录结构
        parts = [p for p in name.split("/") if p]  # 去除空字符串

        current = root
        for part in parts[:-1]:  # 遍历到倒数第二级（父目录）
            if part not in current:
                current[part] = {}
            current = current[part]

        # 最后一级：判断是文件还是目录
        last_part = parts[-1] if parts else None
        if last_part:
            # 即使 ZIP 中没有显式的 dir 条目，只要路径存在就视为可能的目录
            # 但如果 name 以 '/' 结尾，则明确是目录
            if name.endswith("/"):
                # 明确的目录
                if last_part not in current:
                    current[last_part] = {}
                # children 留空，后续可能被填充
            else:
                # 文件：用特殊标记区分
                current[last_part] = "__FILE__"

    # 将嵌套 dict 转换为指定格式的 list of dict
    def dict_to_tree(d: dict):
        result = []
        for name, value in d.items():
            if value == "__FILE__":
                result.append({"name": name, "type": "file", "children": []})
            else:
                # 是目录
                result.append(
                    {"name": name, "type": "dir", "children": dict_to_tree(value)}
                )
        return result

    return dict_to_tree(root)
