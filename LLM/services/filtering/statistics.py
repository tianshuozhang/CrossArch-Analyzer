"""
统计工具模块

提供通用的统计分析功能，用于筛选和审计过程中的数据统计。
"""
import os
from collections import defaultdict
from typing import Dict, List, Tuple


class DirectoryStatistics:
    """目录统计工具"""
    
    @staticmethod
    def calculate_directory_coverage(
        all_files: List[str], 
        kept_files: set, 
        max_depth: int = 2
    ) -> Dict[str, Dict[str, int]]:
        """
        计算目录覆盖率
        
        Args:
            all_files: 所有文件路径列表
            kept_files: 保留文件集合
            max_depth: 最大目录深度
            
        Returns:
            目录统计字典，键为目录路径，值为包含 total 和 kept 的字典
        """
        dir_stats = defaultdict(lambda: {"total": 0, "kept": 0})
        
        for f in all_files:
            # 提取目录路径
            dir_path = DirectoryStatistics._extract_directory(f, max_depth)
            dir_stats[dir_path]["total"] += 1
            if f in kept_files:
                dir_stats[dir_path]["kept"] += 1
        
        return dict(dir_stats)
    
    @staticmethod
    def _extract_directory(path: str, max_depth: int) -> str:
        """
        提取目录路径
        
        Args:
            path: 文件路径
            max_depth: 最大深度
            
        Returns:
            目录路径字符串
        """
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        
        if len(parts) > max_depth:
            return "/".join(parts[:max_depth])
        elif len(parts) > 1:
            return "/".join(parts[:-1])
        else:
            return "[Root]"
    
    @staticmethod
    def calculate_critical_directory_stats(
        all_files: List[str],
        kept_files: set,
        critical_dirs: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        计算核心目录统计
        
        Args:
            all_files: 所有文件路径列表
            kept_files: 保留文件集合
            critical_dirs: 核心目录名称列表
            
        Returns:
            核心目录统计字典
        """
        stats = {}
        
        for critical_dir in critical_dirs:
            matching_files = [
                f for f in all_files 
                if f"/{critical_dir}/" in f.replace("\\", "/").lower() 
                or f.replace("\\", "/").lower().startswith(f"{critical_dir}/")
            ]
            
            if matching_files:
                kept_count = sum(1 for f in matching_files if f in kept_files)
                
                stats[critical_dir] = {
                    "total": len(matching_files),
                    "kept": kept_count,
                    "ratio": (kept_count / len(matching_files) * 100) if matching_files else 0
                }
        
        return stats


class FileTypeStatistics:
    """文件类型统计工具"""
    
    @staticmethod
    def calculate_extension_stats(
        all_files: List[str],
        kept_files: set
    ) -> Dict[str, Dict[str, int]]:
        """
        计算文件扩展名统计
        
        Args:
            all_files: 所有文件路径列表
            kept_files: 保留文件集合
            
        Returns:
            扩展名统计字典
        """
        ext_stats = defaultdict(lambda: {"total": 0, "kept": 0})
        
        for f in all_files:
            ext = os.path.splitext(f)[1].lower()
            if not ext:
                ext = "(无扩展名)"
            ext_stats[ext]["total"] += 1
            if f in kept_files:
                ext_stats[ext]["kept"] += 1
        
        return dict(ext_stats)


class FileSizeStatistics:
    """文件大小统计工具"""
    
    SIZE_RANGES = [
        ("< 1KB", 0, 1024),
        ("1KB - 10KB", 1024, 10*1024),
        ("10KB - 100KB", 10*1024, 100*1024),
        ("> 100KB", 100*1024, float('inf'))
    ]
    
    @staticmethod
    def calculate_size_stats(
        all_files: List[str],
        all_files_content: Dict[str, str],
        kept_files: set
    ) -> Dict[str, Dict[str, float]]:
        """
        计算文件大小分布统计
        
        Args:
            all_files: 所有文件路径列表
            all_files_content: 文件内容字典
            kept_files: 保留文件集合
            
        Returns:
            大小分布统计字典
        """
        size_stats = {}
        
        for label, min_size, max_size in FileSizeStatistics.SIZE_RANGES:
            matching_files = []
            for f in all_files:
                try:
                    file_size = len(all_files_content.get(f, ""))
                    if min_size <= file_size < max_size:
                        matching_files.append(f)
                except Exception:
                    pass
            
            if matching_files:
                kept_count = sum(1 for f in matching_files if f in kept_files)
                size_stats[label] = {
                    "total": len(matching_files),
                    "kept": kept_count,
                    "ratio": (kept_count / len(matching_files) * 100) if matching_files else 0
                }
        
        return size_stats


class KeywordStatistics:
    """关键词统计工具"""
    
    SUSPICIOUS_KEYWORDS = [
        "sched", "task", "thread", "memory", "alloc", "interrupt", "irq", 
        "dispatch", "hal_", "os_", "arch", "bsp"
    ]
    
    @staticmethod
    def find_suspicious_files(
        dropped_files: List[str],
        keywords: List[str] = None
    ) -> List[str]:
        """
        查找包含可疑关键词的文件
        
        Args:
            dropped_files: 被丢弃的文件列表
            keywords: 关键词列表，如果为 None 则使用默认关键词
            
        Returns:
            可疑文件列表
        """
        if keywords is None:
            keywords = KeywordStatistics.SUSPICIOUS_KEYWORDS
        
        suspicious = []
        for f in dropped_files:
            f_lower = f.lower()
            if any(kw in f_lower for kw in keywords):
                suspicious.append(f)
        
        return suspicious

