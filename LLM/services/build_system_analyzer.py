import os
import re
import logging
from typing import Dict, List, Set

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BuildSystemAnalyzer:
    """
    分析项目的构建系统文件（如 Makefile, CMakeLists.txt），
    提取与指令集架构相关的编译选项和宏定义。
    """

    def __init__(self, project_root: str):
        """
        初始化分析器。

        Args:
            project_root (str): 项目的根目录路径。
        """
        self.project_root = project_root
        # 预编译正则表达式，提高性能
        # 匹配 -march=xxx, -mtune=xxx, -mabi=xxx, --target=xxx
        self.arch_flag_pattern = re.compile(
            r"(?:-march|-mtune|-mabi|--target)=([\w\d\.\-_]+)"
        )
        # 匹配 -DXXX, add_definitions(-DXXX), target_compile_definitions(target PRIVATE XXX)
        self.define_pattern = re.compile(
            r"(?:-D|add_definitions\s*\(\s*-D|target_compile_definitions\s*\(\s*\w+\s+\w+\s+)([\w\d_]+)"
        )

    def analyze(self) -> Dict[str, Set[str]]:
        """
        自动检测并分析项目根目录下的构建文件。
        目前支持 CMakeLists.txt 和 Makefile。
        """
        cmake_path = os.path.join(self.project_root, 'CMakeLists.txt')
        makefile_path = os.path.join(self.project_root, 'Makefile')

        if os.path.exists(cmake_path):
            logger.info("检测到 CMakeLists.txt，开始分析...")
            return self._analyze_file(cmake_path)
        elif os.path.exists(makefile_path):
            logger.info("检测到 Makefile，开始分析...")
            return self._analyze_file(makefile_path)
        else:
            logger.warning("在项目根目录未找到支持的构建文件 (CMakeLists.txt or Makefile)。")
            return {"arch_flags": set(), "definitions": set()}

    def _analyze_file(self, file_path: str) -> Dict[str, Set[str]]:
        """
        使用正则表达式从单个文件中提取信息。

        Args:
            file_path (str): 构建文件的路径。

        Returns:
            Dict[str, Set[str]]: 包含架构标志和宏定义的字典。
        """
        arch_flags = set()
        definitions = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 提取所有匹配的架构相关编译选项
                for match in self.arch_flag_pattern.finditer(content):
                    arch_flags.add(match.group(0)) # group(0) 获取完整匹配, e.g., "-march=armv8-a"
                
                # 提取所有 `-D` 宏定义
                for match in self.define_pattern.finditer(content):
                    definitions.add(match.group(1)) # group(1) 获取捕获组内容, e.g., "USE_NEON"
        
        except Exception as e:
            logger.error(f"分析文件 {file_path} 时出错: {e}")
            
        logger.info(f"分析完成: 找到 {len(arch_flags)} 个架构标志, {len(definitions)} 个宏定义。")
        return {"arch_flags": arch_flags, "definitions": definitions}