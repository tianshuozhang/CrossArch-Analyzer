import logging
from collections import defaultdict
from typing import List, Dict, Any, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrossFileCorrelator:
    """
    聚合所有单文件的分析报告，通过跨文件关联分析，发现项目级的架构兼容性问题。
    例如，检测一个函数在某些架构上有实现，但在其他架构上缺失。
    """

    def __init__(self, all_reports: List[Dict[str, Any]]):
        """
        初始化关联器。

        Args:
            all_reports (List[Dict[str, Any]]): 
                一个包含项目中所有文件分析报告的列表。
                每个报告应包含 'file_path', 'defined_functions', 'called_functions' 等键。
        """
        self.all_reports = all_reports
        # 全局符号表: Dict[function_name, Dict[architecture, file_path]]
        self.symbol_table: Dict[str, Dict[str, str]] = defaultdict(dict)
        # 全局调用表: Dict[function_name, List[caller_file_path]]
        self.call_graph: Dict[str, List[str]] = defaultdict(list)
        # 项目中出现过的所有特定架构的集合
        self.project_architectures: Set[str] = set()

    def _build_symbol_table(self):
        """
        遍历所有报告，构建全局的符号->架构实现表和调用图。
        """
        logger.info("正在构建全局符号表和调用图...")
        for report in self.all_reports:
            file_path = report.get('file_path', 'unknown_file')
            
            # 聚合函数定义
            for func in report.get('defined_functions', []):
                func_name = func.get('name')
                architecture = func.get('architecture', 'Generic') # 默认为架构无关
                if func_name:
                    self.symbol_table[func_name][architecture] = file_path
                    if architecture != 'Generic':
                        self.project_architectures.add(architecture)
                        
            # 聚合函数调用
            for func_call in report.get('called_functions', []):
                func_name = func_call.get('name')
                if func_name:
                    self.call_graph[func_name].append(file_path)
        logger.info("全局符号表构建完成。")

    def find_missing_implementations(self) -> List[Dict[str, Any]]:
        """
        核心分析逻辑：查找多版本实现的缺失问题。

        如果一个函数在一个架构上有特定实现，但在另一个已知的项目架构上没有，
        并且这个函数在项目中被调用过，就认为这是一个风险。

        Returns:
            List[Dict[str, Any]]: 一个包含所有检测到的缺失实现问题的列表。
        """
        self._build_symbol_table()
        
        issues = []
        
        # 遍历所有被定义过的函数
        for func_name, implementations in self.symbol_table.items():
            implemented_archs = {arch for arch in implementations.keys() if arch != 'Generic'}
            
            # 检查条件：
            # 1. 该函数至少有一个架构特定版本。
            # 2. 该函数被项目代码调用过。
            # 3. 存在一个项目架构，但该函数没有为其提供实现。
            if implemented_archs and func_name in self.call_graph:
                unimplemented_archs = self.project_architectures - implemented_archs
                
                # 如果有缺失的实现，并且没有通用的'Generic'实现作为后备
                if unimplemented_archs and 'Generic' not in implementations:
                    issue = {
                        "type": "MissingMultiArchImplementation",
                        "function_name": func_name,
                        "implemented_in": {k: v for k, v in implementations.items()},
                        "missing_for_arch": list(unimplemented_archs),
                        "called_from": list(set(self.call_graph[func_name])),
                        "suggestion": f"函数 '{func_name}' 在项目中被调用，并为 {list(implemented_archs)} 提供了特定实现，但缺少 {list(unimplemented_archs)} 版本。请提供缺失的实现或一个通用的后备实现。"
                    }
                    issues.append(issue)
                    logger.warning(f"发现问题: {issue['suggestion']}")

        return issues