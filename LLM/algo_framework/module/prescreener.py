from utils.data_structures import *
import sys
sys.path.append('LLM/')
from agents.file_utils import FileScanner, ArchitectureHeuristics

class PreScreener:
    def prescreen(project_root: str) -> list[str]:
        # TODO:读取project_root下面的内容，预筛选，然后文件到临时目录，然后返回<list[旧的路径],list[新的路径]>
        # 扫描项目文件
        file_scanner = FileScanner(project_root)
        files = file_scanner.scan_all_files()
        source_files = files['source_files']
        
        pre_screened = []

        for file_path in source_files:
            is_arch, _ = ArchitectureHeuristics.is_likely_arch_related(file_path, None)
            if is_arch:
                pre_screened.append(file_path)

        return source_files, pre_screened
