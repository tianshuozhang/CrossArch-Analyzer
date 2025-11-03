from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CodeClassification:
    """代码分类结果"""
    file_path: str
    line_number: int
    category: str  # ARM, x86, RISC-V, Architecture-Independent, Conflict
    reasoning: str
    evidence: List[str]

class RuleEngine:
    """基于规则的代码分类推理引擎"""
    
    def __init__(self):
        self.conflict_resolution_rules = [
            self._resolve_same_arch_conflict,
            self._resolve_different_arch_conflict,
            self._resolve_no_evidence_case
        ]
    
    def _resolve_same_arch_conflict(self, preprocessor_arch, asm_arch, intrinsic_arch, evidence):
        """解决相同架构冲突"""
        # 检查是否所有证据指向同一架构
        archs = [arch for arch in [preprocessor_arch, asm_arch, intrinsic_arch] if arch]
        unique_archs = set(archs)
        
        if len(unique_archs) == 1:
            arch = unique_archs.pop()
            return arch, f"所有证据都指向 {arch} 架构"
        
        return None, "需要进一步分析"
    
    def _resolve_different_arch_conflict(self, preprocessor_arch, asm_arch, intrinsic_arch, evidence):
        """解决不同架构冲突"""
        # 当证据指向不同架构时的处理逻辑
        archs = [arch for arch in [preprocessor_arch, asm_arch, intrinsic_arch] if arch]
        unique_archs = set(archs)
        
        if len(unique_archs) > 1:
            # 这里可以添加优先级逻辑，比如预处理宏的权重更高
            if preprocessor_arch:
                return preprocessor_arch, f"预处理宏指示 {preprocessor_arch} 架构，优先级较高"
            elif asm_arch:
                return asm_arch, f"内联汇编指示 {asm_arch} 架构"
        
        return None, "需要进一步分析"
    
    def _resolve_no_evidence_case(self, preprocessor_arch, asm_arch, intrinsic_arch, evidence):
        """处理无证据情况"""
        if not any([preprocessor_arch, asm_arch, intrinsic_arch]):
            return "Architecture-Independent", "未检测到架构相关代码"
        
        return None, "需要进一步分析"

    def classify_code(self, file_path: str, code: str, 
                      preprocessor_results: List[Dict],
                      asm_results: List[Dict], 
                      intrinsics_results: List[Dict]) -> List[CodeClassification]:
        """
        综合所有分析结果进行代码分类
        
        Args:
            file_path: 源代码文件路径
            code: 源代码内容
            preprocessor_results: 预处理分析结果
            asm_results: 内联汇编分析结果  
            intrinsics_results: 内置函数分析结果
            
        Returns:
            代码行分类结果列表
        """
        lines = code.split('\n')
        classifications = []
        
        for line_num in range(1, len(lines) + 1):
            classification = self._classify_single_line(
                line_num, file_path, preprocessor_results, 
                asm_results, intrinsics_results
            )
            classifications.append(classification)
        
        return classifications
    
    def _classify_single_line(self, line_num: int, file_path: str,
                            preprocessor_results: List[Dict],
                            asm_results: List[Dict],
                            intrinsics_results: List[Dict]) -> CodeClassification:
        """分类单行代码"""
        # 收集该行的所有证据
        evidence = []
        
        # 检查预处理宏
        preprocessor_arch = self._get_arch_from_preprocessor(line_num, preprocessor_results)
        if preprocessor_arch:
            evidence.append(f"Preprocessor macro: {preprocessor_arch}")
        
        # 检查内联汇编
        asm_arch = self._get_arch_from_asm(line_num, asm_results)
        if asm_arch:
            evidence.append(f"Inline assembly: {asm_arch}")
        
        # 检查内置函数
        intrinsic_arch = self._get_arch_from_intrinsics(line_num, intrinsics_results)
        if intrinsic_arch:
            evidence.append(f"Intrinsic function: {intrinsic_arch}")
        
        # 应用冲突解决规则
        category, reasoning = self._apply_conflict_resolution_rules(
            preprocessor_arch, asm_arch, intrinsic_arch, evidence
        )
        
        return CodeClassification(
            file_path=file_path,
            line_number=line_num,
            category=category,
            reasoning=reasoning,
            evidence=evidence
        )
    
    def _apply_conflict_resolution_rules(self, preprocessor_arch: str,
                                       asm_arch: str, intrinsic_arch: str,
                                       evidence: List[str]) -> tuple:
        """应用冲突解决规则"""
        archs = [arch for arch in [preprocessor_arch, asm_arch, intrinsic_arch] if arch]
        
        if not archs:
            return "Architecture-Independent", "No architecture-specific code detected"
        
        # 检查是否所有证据指向同一架构
        unique_archs = set(archs)
        if len(unique_archs) == 1:
            arch = unique_archs.pop()
            return arch, f"All evidence points to {arch} architecture"
        
        # 架构冲突
        return "Conflict", f"Architecture conflict detected: {', '.join(unique_archs)}"
    
    def _get_arch_from_preprocessor(self, line_num: int, results: List[Dict]) -> str:
        """从预处理结果获取架构信息"""
        for result in results:
            if result['start_line'] <= line_num <= result['end_line']:
                return result['arch']
        return None
    
    def _get_arch_from_asm(self, line_num: int, results: List[Dict]) -> str:
        """从内联汇编结果获取架构信息"""
        for result in results:
            if result['line_number'] == line_num:
                return result['arch']
        return None
    
    def _get_arch_from_intrinsics(self, line_num: int, results: List[Dict]) -> str:
        """从内置函数结果获取架构信息"""
        for result in results:
            if result['line_number'] == line_num:
                return result['arch']
        return None
