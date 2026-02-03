import json

from db.db_project import ProjectDB
from db.db_file import FileDB
from db.db_user import UserDB

from utils.path import *
from utils.zip import *

user_db = UserDB()
project_db = ProjectDB()
file_db = FileDB()


def execute_close_project(user_id: int, project_id: int):
    # === 1. 把项目保存到指定位置 ===
    try:
        zip_pack_dir_to(
            src_root_dir_path=path_dir_open(user_id),
            dst_zip_path=path_file_save_zip(user_id, project_id),
        )
    except Exception as e:
        print(f"WARNING: 保存项目时出错: {e}")
    # === 2. 清理open目录，更新用户的open_project_id===
    try:
        path_tool_clean_dir(path_dir_open(user_id))
    except Exception as e:
        print(f"WARNING: 清理目录时出错: {e}")
    if not user_db.update_opened_project_id(user_id, 0):
        print("ERROR:更新用户已打开项目失败")
        # 即使更新失败，也继续执行，避免阻塞


def execute_open_project(user_id: int, project_id: int):
    # === 1. 如果用户已打开的和要打开的项目一样，那么直接返回 ===
    opened_project_id = user_db.get_opened_project_id(user_id)
    if opened_project_id == project_id:
        return True
    # === 2. 检查用户是否有已打开的项目，如果有，那么关闭它 ===
    if opened_project_id is not None and opened_project_id != 0:
        try:
            execute_close_project(user_id, opened_project_id)
        except Exception as e:
            print(f"WARNING: 关闭旧项目时出错: {e}，继续打开新项目")

    # === 3. 打开项目 ===
    zip_extract_file_to(
        src_zip_path=path_file_save_zip(user_id, project_id),
        dst_dir_path=path_dir_open(user_id),
    )
    # === 4. 更新用户已打开项目 ===
    if not user_db.update_opened_project_id(user_id, project_id):
        raise ValueError("更新用户已打开项目失败")


def register_project_files(zip_path: str, project_id: int):
    for file_path in zip_read_namelist(zip_path):
        file_db.add_file(
            name=path_tool_basename(file_path),
            project_id=project_id,
            path=file_path,
        )


def make_file_tree_from_zip(zip_path: str) -> list:
    """
    递归构建目录树
    返回：[{name: "", type: "dir/file", children: []}]
    """
    namelist = zip_read_namelist(zip_path)

    def _make_a_tree(namelist: list[str]):
        root = {}
        # 构建虚拟文件系统（扁平路径 → 嵌套结构）
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
        return root

    # 将嵌套 dict 转换为指定格式的 list of dict
    def _dict_to_tree(d: dict):
        result = []
        for name, value in d.items():
            if value == "__FILE__":
                result.append({"name": name, "type": "file", "children": []})
            else:
                # 是目录
                result.append(
                    {"name": name, "type": "dir", "children": _dict_to_tree(value)}
                )
        return result

    return _dict_to_tree(_make_a_tree(namelist))


def save_file_tree_to_zip(zip_path: str, tree: list):
    zip_add_to_zip(zip_path, [("tree.json", json.dumps(tree, indent=2))])


def read_file_tree_from_zip(user_id: int, project_id: int):
    zip_path = path_file_save_zip(user_id, project_id)
    content = zip_read_file_from_zip(zip_path, "tree.json")
    project_tree = json.loads(content)
    return project_tree
