"""
文件处理工具模块 - 扫描项目文件、构建文件树、读取文件内容
"""
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class FileScanner:
    """项目文件扫描器"""
    
    # 常见的C/C++源文件扩展名
    SOURCE_EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx', '.hh'}
    
    # 构建配置文件
    BUILD_FILES = {'CMakeLists.txt', 'Makefile', 'makefile', 'GNUmakefile'}
    
    # 文档文件
    DOC_FILES = {'README.md', 'README', 'README.txt', 'INSTALL', 'INSTALL.md'}
    
    # 需要忽略的目录
    IGNORE_DIRS = {'.git', '.svn', 'build', 'bin', 'obj', '__pycache__', 'node_modules'}
    
    def __init__(self, project_path: str):
        """
        初始化文件扫描器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")
        
        if not self.project_path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {project_path}")
    
    def scan_all_files(self) -> Dict[str, List[str]]:
        """
        扫描项目中的所有相关文件
        
        Returns:
            分类后的文件字典，包含：
            - source_files: C/C++源文件列表
            - build_files: 构建配置文件列表
            - doc_files: 文档文件列表
        """
        result = {
            'source_files': [],
            'build_files': [],
            'doc_files': []
        }
        
        for root, dirs, files in os.walk(self.project_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                if not file_path.is_file():
                    continue
                relative_path = str(file_path.relative_to(self.project_path))
                
                # 分类文件
                if file in self.BUILD_FILES:
                    result['build_files'].append(relative_path)
                elif file in self.DOC_FILES:
                    result['doc_files'].append(relative_path)
                elif file_path.suffix in self.SOURCE_EXTENSIONS:
                    result['source_files'].append(relative_path)
        
        return result
    
    def build_file_tree(self, max_depth: int = 3) -> str:
        """
        构建项目的文件树字符串表示
        
        Args:
            max_depth: 最大递归深度
        
        Returns:
            文件树的字符串表示
        """
        tree_lines = [f"📁 {self.project_path.name}/"]
        
        def _add_tree_items(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return
            
            # 过滤忽略的目录
            items = [item for item in items if item.name not in self.IGNORE_DIRS]
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    tree_lines.append(f"{prefix}{connector}📁 {item.name}/")
                    extension = "    " if is_last else "│   "
                    _add_tree_items(item, prefix + extension, depth + 1)
                else:
                    icon = "📄"
                    if item.suffix in self.SOURCE_EXTENSIONS:
                        icon = "💻"
                    elif item.name in self.BUILD_FILES:
                        icon = "⚙️"
                    elif item.name in self.DOC_FILES:
                        icon = "📖"
                    
                    tree_lines.append(f"{prefix}{connector}{icon} {item.name}")
        
        _add_tree_items(self.project_path)
        return "\n".join(tree_lines)
    
    def read_file(self, relative_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Optional[str]:
        """
        读取文件内容，支持分段读取以节省上下文空间
        
        Args:
            relative_path: 相对于项目根目录的文件路径
            start_line: 起始行号 (从1开始计数)
            end_line: 结束行号
        
        Returns:
            文件内容字符串或切片后的内容，失败返回None
        """
        file_path = (self.project_path / relative_path).resolve()
        
        # 安全检查：必须存在且是文件（防止 Permission denied）
        if not file_path.exists() or not file_path.is_file():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 情况 1: 如果没有指定行号，直接读取全文（慎用）
                if start_line is None and end_line is None:
                    return f.read()
                
                # 情况 2: 高效读取指定行范围
                content_lines = []
                current_line = 1
                
                # 使用迭代器逐行读取，避免大文件一次性装入内存
                for line in f:
                    if start_line and current_line < start_line:
                        current_line += 1
                        continue
                    if end_line and current_line > end_line:
                        break
                    
                    content_lines.append(line)
                    current_line += 1
                
                header = f"--- [File: {relative_path} | Lines {start_line or 1} to {current_line-1}] ---\n"
                return header + "".join(content_lines)
                
        except Exception as e:
            print(f"❌ 读取文件失败 {relative_path}: {e}")
            return None
    
    def get_file_info(self, relative_path: str) -> Optional[Dict[str, any]]:
        """
        获取文件的元信息
        
        Args:
            relative_path: 相对于项目根目录的文件路径
        
        Returns:
            文件信息字典，包含size, lines等
        """
        file_path = self.project_path / relative_path
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            content = self.read_file(relative_path)
            
            return {
                'path': relative_path,
                'name': file_path.name,
                'size': stat.st_size,
                'lines': len(content.splitlines()) if content else 0,
                'extension': file_path.suffix
            }
        except Exception as e:
            print(f"❌ 获取文件信息失败 {relative_path}: {e}")
            return None
    
    def batch_read_files(self, relative_paths: List[str]) -> Dict[str, str]:
        """
        批量读取文件内容
        
        Args:
            relative_paths: 相对路径列表
        
        Returns:
            文件路径到内容的映射字典
        """
        result = {}
        
        for path in relative_paths:
            content = self.read_file(path)
            if content is not None:
                result[path] = content
        
        return result


class ArchitectureHeuristics:
    """架构相关性启发式规则"""
    
    # 架构相关的路径关键词
    ARCH_PATH_KEYWORDS = [
        'arch', 'platform', 'asm', 'cpu', 'mach',
        'arm', 'x86', 'riscv', 'mips', 'powerpc',
        'aarch64', 'i386', 'x86_64'
    ]
    
    # 架构相关的宏定义
    ARCH_MACROS = [
        '__arm__', '__aarch64__', '__x86_64__', '__i386__',
        '__riscv', '__mips__', '__powerpc__',
        'CONFIG_ARM', 'CONFIG_X86', 'CONFIG_RISCV',
        'ARCH_', 'PLATFORM_'
        # , 'CPU_'
    ]
    
    # 架构相关的文件名模式
    ARCH_FILENAME_PATTERNS = [
        '_arm', '_x86', '_riscv', '_mips',
        'arm_', 'x86_', 'riscv_', 'mips_',
        'arch', 'platform'
        # , 'cpu'
    ]
    
    @staticmethod
    def is_likely_arch_related(file_path: str, file_content: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        判断文件是否可能架构相关
        
        Args:
            file_path: 文件路径
            file_content: 文件内容(可选)
        
        Returns:
            (是否架构相关, 匹配的原因列表)
        """
        reasons = []
        
        # 检查路径
        file_path_lower = file_path.lower()
        for keyword in ArchitectureHeuristics.ARCH_PATH_KEYWORDS:
            if keyword in file_path_lower:
                reasons.append(f"路径包含架构关键词: {keyword}")
        
        # 检查文件名
        filename = os.path.basename(file_path_lower)

        for pattern in ArchitectureHeuristics.ARCH_FILENAME_PATTERNS:
            if pattern in filename:
                reasons.append(f"文件名包含架构模式: {pattern}")
        
        # 如果提供了文件内容，检查宏定义
        if file_content:
            for macro in ArchitectureHeuristics.ARCH_MACROS:
                if macro in file_content:
                    reasons.append(f"代码包含架构宏: {macro}")
                    break  # 找到一个就够了
        
        return (len(reasons) > 0, reasons)