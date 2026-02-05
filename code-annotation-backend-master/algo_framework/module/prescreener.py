import os
import shutil
import tempfile
from pathlib import Path
import sys

sys.path.append("LLM/")
sys.path.append("")
from utils.data_structures import *
from utils.file_utils import FileScanner
from utils.engine import FilePreScreener


class PreScreener:
    @staticmethod
    def _load_all_source_files(project_root: str):
        # TODO:加载项目中的所有源文件内容（支持所有 C/C++ 文件类型）
        file_contents = {}
        file_scanner = FileScanner(project_root)
        files = file_scanner.scan_all_files()
        all_source_files = files["source_files"]

        print(f"正在加载 {len(all_source_files)} 个源文件...")

        for file_path in all_source_files:
            try:
                file_path_str = str(file_path)
                with open(file_path_str, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                file_contents[file_path_str] = content
            except UnicodeDecodeError:
                print(f"警告: 文件 '{file_path}' 编码错误，跳过。")
            except Exception as e:
                print(f"错误: 无法读取文件 '{file_path}': {e}")

        print(f"文件加载完成。总计加载了 {len(file_contents)} 个文件。")
        return file_contents

    @staticmethod
    def prescreen(project_root: str):
        # TODO:读取project_root下面的内容，预筛选，然后文件到临时目录，然后返回<list[旧的路径],list[新的路径]>
        all_files = PreScreener._load_all_source_files(project_root)

        if not all_files:
            print("警告: 未找到任何文件")
            return [], []

        print(f"正在预筛选文件 (总数: {len(all_files)})...")
        pre_screener = FilePreScreener()
        kept_files = pre_screener.filter_files(all_files)
        print(f"预筛选完成: 保留 {len(kept_files)}/{len(all_files)} 个文件")

        temp_dir = tempfile.mkdtemp(prefix="prescreened_")
        print(f"创建临时目录: {temp_dir}")

        old_paths = []
        new_paths = []
        project_root_path = Path(project_root).resolve()

        def _copy_file(old_path):
            # 计算相对路径并复制文件到临时目录，保持目录结构
            try:
                old_path_obj = Path(old_path)
                if old_path_obj.is_absolute():
                    try:
                        rel_path = old_path_obj.relative_to(project_root_path)
                    except ValueError:
                        rel_path = Path(old_path_obj.name)
                else:
                    rel_path = Path(old_path)

                new_path_obj = Path(temp_dir) / rel_path
                new_path_obj.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_path, new_path_obj)

                old_paths.append(str(old_path))
                new_paths.append(str(new_path_obj))
            except Exception as e:
                print(f"警告: 无法复制文件 {old_path}: {e}")

        for old_path in kept_files:
            _copy_file(old_path)

        print(f"文件复制完成: {len(new_paths)} 个文件已复制到临时目录")
        return old_paths, new_paths
