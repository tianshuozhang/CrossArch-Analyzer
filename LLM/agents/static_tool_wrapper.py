"""
静态分析工具包装器 - 优化版：提供更精确的失败位置信息
"""
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from core.Static_CodeAnalyzer import Static_CodeAnalyzer


class StaticAnalysisWrapper:
    """静态代码分析工具的包装类 - 优化版"""
    
    def __init__(self):
        self.analyzer = Static_CodeAnalyzer()
    
    def analyze_file(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        分析单个文件的架构依赖
        
        Returns:
            包含status, 架构信息, 或失败详情的字典
        """
        try:
            analysis_result, error_lines = self.analyzer.scan_code(code_content)
            
            if error_lines is not None:
                # 解析失败 - 尝试提取更精确的位置信息
                failed_line = self._extract_error_line(error_lines, code_content)
                
                return {
                    'file_path': file_path,
                    'status': 'failed',
                    'error': f"解析失败",
                    'line_number': failed_line,
                    'context_hint': self._get_context_hint(code_content, failed_line)
                }
            
            # 解析成功 - 提取结构化信息
            result = self._structure_analysis_result(file_path, analysis_result)
            return result
            
        except Exception as e:
            # 运行时异常
            return {
                'file_path': file_path,
                'status': 'error',
                'error': str(e),
                'line_number': 'unknown'
            }
    
    def batch_analyze_files(self, files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """批量分析多个文件"""
        results = {}
        total = len(files_content)
        
        for i, (file_path, content) in enumerate(files_content.items(), 1):
            if i % 10 == 0:
                print(f"  处理进度: {i}/{total}")
            results[file_path] = self.analyze_file(file_path, content)
        
        return results
    
    def _extract_error_line(self, error_lines: Any, code_content: str) -> int:
        """
        从错误信息中提取失败的行号
        
        Args:
            error_lines: 错误行信息（可能是字符串、元组或其他）
            code_content: 源代码内容
        
        Returns:
            估计的失败行号
        """
        # 尝试从error_lines中提取数字
        if isinstance(error_lines, (int, float)):
            return int(error_lines)
        
        if isinstance(error_lines, str):
            # 尝试从字符串中提取行号 (如 "line 105" 或 "105")
            numbers = re.findall(r'\d+', error_lines)
            if numbers:
                return int(numbers[0])
        
        if isinstance(error_lines, (tuple, list)) and error_lines:
            # 可能是 (line_num, col_num) 元组
            if isinstance(error_lines[0], (int, float)):
                return int(error_lines[0])
        
        # 如果无法提取，返回一个中间行号作为猜测
        lines = code_content.split('\n')
        return len(lines) // 2
    
    def _get_context_hint(self, code_content: str, line_number: int) -> str:
        """
        获取失败位置附近的上下文提示
        
        Returns:
            简短的上下文描述（不包含完整代码）
        """
        lines = code_content.split('\n')
        
        if line_number == 'unknown' or line_number <= 0 or line_number > len(lines):
            return "建议从头开始检查宏定义和条件编译"
        
        # 获取失败行附近的非空行
        start = max(0, line_number - 3)
        end = min(len(lines), line_number + 3)
        
        context_lines = []
        for i in range(start, end):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith('//'):
                context_lines.append(stripped[:50])  # 只取前50个字符
        
        # 检查是否涉及宏定义
        has_macro = any('#' in line for line in context_lines)
        has_ifdef = any('ifdef' in line or 'ifndef' in line for line in context_lines)
        
        hints = []
        if has_macro:
            hints.append("涉及宏定义")
        if has_ifdef:
            hints.append("涉及条件编译")
        
        return f"失败位置约在第{line_number}行附近，" + "，".join(hints) if hints else "常规代码"
    
    def _structure_analysis_result(self, file_path: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """将原始分析结果转换为结构化格式"""
        tagged_symbols = analysis_result.get('taggedSymbols', {})
        tagged_targets = analysis_result.get('taggedTargets', [])
        
        # 统计架构依赖
        arch_statistics = self._compute_arch_statistics(tagged_symbols)
        
        # 确定主导架构
        dominant_arch = self._determine_dominant_arch(arch_statistics)
        
        # 提取架构相关的代码块
        arch_related_blocks = self._extract_arch_blocks(tagged_targets)
        
        # 提取架构相关的符号
        arch_related_symbols = {
            symbol: arch 
            for symbol, arch in tagged_symbols.items() 
            if arch not in ['common', 'irrelevant']
        }
        
        return {
            'file_path': file_path,
            'status': 'success',
            'dominant_architecture': dominant_arch,
            'architecture_statistics': arch_statistics,
            'arch_related_symbols': arch_related_symbols,
            'arch_related_blocks': arch_related_blocks,
            'total_symbols': len(tagged_symbols),
            'total_blocks': len(tagged_targets)
        }
    
    def _compute_arch_statistics(self, tagged_symbols: Dict[str, str]) -> Dict[str, int]:
        """计算架构依赖统计信息"""
        stats = {}
        for arch in tagged_symbols.values():
            if arch not in ['common', 'irrelevant']:
                stats[arch] = stats.get(arch, 0) + 1
        return stats
    
    def _determine_dominant_arch(self, arch_statistics: Dict[str, int]) -> str:
        """确定主导架构"""
        if not arch_statistics:
            return 'Generic'
        
        # 返回数量最多的架构
        return max(arch_statistics.items(), key=lambda x: x[1])[0]
    
    def _extract_arch_blocks(self, tagged_targets: List[Tuple[str, Tuple[int, int], List[str]]]) -> List[Dict[str, Any]]:
        """
        提取架构相关的代码块信息
        
        Args:
            tagged_targets: [(target_name, (start, end), [arch_tags])]
        
        Returns:
            架构相关代码块的列表
        """
        arch_blocks = []
        
        for target_name, (start_line, end_line), arch_tags in tagged_targets:
            # 过滤掉纯common或irrelevant的块
            relevant_archs = [
                arch for arch in arch_tags 
                if arch not in ['common', 'irrelevant']
            ]
            
            if relevant_archs:
                arch_blocks.append({
                    'start_line': start_line,
                    'end_line': end_line,
                    'architecture': relevant_archs[0] if len(relevant_archs) == 1 else 'Multi',
                    'architectures': relevant_archs,
                    'code_fragment': target_name[:50] if target_name else '',
                    'reason': f"Detected {', '.join(relevant_archs)} specific code"
                })
        
        return arch_blocks
    
    def summarize_project_analysis(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """汇总整个项目的分析结果"""
        summary = {
            'total_files_analyzed': len(all_results),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'global_arch_statistics': {},
            'files_by_architecture': {},
            'multi_arch_files': [],
            'arch_free_files': []
        }
        
        for file_path, result in all_results.items():
            if result['status'] == 'success':
                summary['successful_analyses'] += 1
                
                arch_stats = result.get('architecture_statistics', {})
                
                # 全局架构统计
                for arch, count in arch_stats.items():
                    summary['global_arch_statistics'][arch] = \
                        summary['global_arch_statistics'].get(arch, 0) + count
                
                # 确定文件的主要架构
                if not arch_stats:
                    summary['arch_free_files'].append(file_path)
                else:
                    if len(arch_stats) > 1:
                        summary['multi_arch_files'].append({
                            'file': file_path,
                            'architectures': list(arch_stats.keys())
                        })
                    
                    dominant = result.get('dominant_architecture', 'Generic')
                    if dominant not in summary['files_by_architecture']:
                        summary['files_by_architecture'][dominant] = []
                    summary['files_by_architecture'][dominant].append(file_path)
            else:
                summary['failed_analyses'] += 1
        
        return summary