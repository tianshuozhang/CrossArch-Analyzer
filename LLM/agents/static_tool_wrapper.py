"""
静态分析工具包装器 - 多区间优化版
核心改进：将多个报错行分组为多个需要分析的区间
"""
from typing import Dict, Any, List, Optional, Tuple
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
LLM_dir = os.path.dirname(current_dir)
sys.path.append(LLM_dir)
from core.Static_CodeAnalyzer import Static_CodeAnalyzer


class ErrorRegion:
    """错误区间数据类"""
    def __init__(self, start_line: int, end_line: int, error_lines: List[int]):
        self.start_line = start_line
        self.end_line = end_line
        self.error_lines = error_lines  # 该区间内的具体报错行
        self.region_id = f"{start_line}-{end_line}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_line': self.start_line,
            'end_line': self.end_line,
            'error_lines': self.error_lines,
            'region_id': self.region_id,
            'line_count': self.end_line - self.start_line + 1
        }


class StaticAnalysisWrapper:
    """静态代码分析工具的包装类 - 多区间优化版"""
    
    def __init__(self, region_size: int = 100):
        """
        Args:
            region_size: 每个区间的行数（默认100行）
        """
        self.analyzer = Static_CodeAnalyzer()
        self.region_size = region_size
    
    def analyze_file(self, file_path: str, code_content: str) -> Dict[str, Any]:
        """
        分析单个文件的架构依赖
        
        Returns:
            包含status, 架构信息, 或失败详情（含多个区间）的字典
        """
        try:
            analysis_result, error_lines = self.analyzer.scan_code(code_content)
            
            if error_lines is not None:
                # 解析失败 - 提取所有报错行并分组为区间
                all_error_lines = sorted(set(error_lines))
                error_regions = self._group_errors_into_regions(all_error_lines, code_content)
                
                return {
                    'file_path': file_path,
                    'status': 'failed',
                    'error': f"解析失败，检测到 {len(all_error_lines)} 个报错行",
                    'total_error_lines': len(all_error_lines),
                    'error_regions': [region.to_dict() for region in error_regions],
                    'needs_manual_analysis': True
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
                'error_regions': []
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
    
    
    
    def _group_errors_into_regions(
        self, 
        error_lines: List[int], 
        code_content: str
    ) -> List[ErrorRegion]:
        """
        将错误行分组为多个需要分析的区间
        
        算法：
        1. 对于每个错误行，创建一个以它为中心的区间（region_size行）
        2. 合并重叠的区间
        3. 确保区间不超出文件边界
        
        Args:
            error_lines: 排序后的错误行号列表
            code_content: 源代码内容
        
        Returns:
            ErrorRegion对象列表
        """
        if not error_lines:
            return []
        
        total_lines = len(code_content.split('\n'))
        half_region = self.region_size // 2
        start = 0
        end = 0
        err: Optional[ErrorRegion] = None

        error_regions: List[ErrorRegion] = []
        for error_line in error_lines:
            # 以错误行为中心，向前后扩展
            if error_line>start and error_line<=end:
                err.error_lines.append(error_line)
                # 已经在当前区间内，跳过
                continue
            if err is not None:
                error_regions.append(err)
            start = max(1, error_line - half_region)
            end = min(total_lines, error_line + half_region)
            err = ErrorRegion(start, end, [error_line])

        error_regions.append(err)
       
        return error_regions
    
    
    
    
    
    def _structure_analysis_result(
        self, 
        file_path: str, 
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        
        return max(arch_statistics.items(), key=lambda x: x[1])[0]
    
    def _extract_arch_blocks(
        self, 
        tagged_targets: List[Tuple[str, Tuple[int, int], List[str]]]
    ) -> List[Dict[str, Any]]:
        """提取架构相关的代码块信息"""
        arch_blocks = []
        
        for target_name, (start_line, end_line), arch_tags in tagged_targets:
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


# ============================================================================
# 测试代码
# ============================================================================

def test_error_grouping():
    """测试错误行分组功能"""
    
    # 模拟一个1000行的文件
    code_content = "\n".join([f"line {i}" for i in range(1, 1001)])
    
    wrapper = StaticAnalysisWrapper(region_size=100)
    
    # 测试用例1: 单个错误
    print("测试1: 单个错误行")
    error_lines = [500]
    regions = wrapper._group_errors_into_regions(error_lines, code_content)
    for region in regions:
        print(f"  区间: {region.start_line}-{region.end_line}, 报错行: {region.error_lines}")
    
    # 测试用例2: 多个分散的错误
    print("\n测试2: 多个分散的错误")
    error_lines = [50, 200, 500, 800]
    regions = wrapper._group_errors_into_regions(error_lines, code_content)
    for region in regions:
        print(f"  区间: {region.start_line}-{region.end_line}, 报错行: {region.error_lines}")
    
    # 测试用例3: 密集的错误（应该合并）
    print("\n测试3: 密集的错误")
    error_lines = [100, 105, 110, 120, 125]
    regions = wrapper._group_errors_into_regions(error_lines, code_content)
    for region in regions:
        print(f"  区间: {region.start_line}-{region.end_line}, 报错行: {region.error_lines}")
    
    # 测试用例4: 边界情况
    print("\n测试4: 边界情况")
    error_lines = [5, 995]
    regions = wrapper._group_errors_into_regions(error_lines, code_content)
    for region in regions:
        print(f"  区间: {region.start_line}-{region.end_line}, 报错行: {region.error_lines}")


if __name__ == "__main__":
    test_error_grouping()