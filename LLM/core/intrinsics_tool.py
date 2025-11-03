import re
from typing import List, Dict, Any

class IntrinsicsTool:
    """架构相关内置函数识别器工具"""
    
    def __init__(self, intrinsics_mapping: Dict[str, str]):
        self.intrinsics_mapping = intrinsics_mapping
        # 匹配函数调用模式
        self.function_pattern = re.compile(r'\b(\w+)\s*\([^)]*\)', re.MULTILINE)
    
    def scan_intrinsics(self, code: str) -> List[Dict[str, Any]]:
        """
        扫描代码中的架构相关内置函数
        
        Args:
            code: 源代码字符串
            
        Returns:
            内置函数的结构化列表
        """
        results = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            functions = self._extract_functions_from_line(line)
            for func_name in functions:
                if func_name in self.intrinsics_mapping:
                    arch = self.intrinsics_mapping[func_name]
                    results.append({
                        'line_number': line_num,
                        'type': 'intrinsic',
                        'function': func_name,
                        'arch': arch,
                        'original_line': line.strip()
                    })
        
        return results
    
    def _extract_functions_from_line(self, line: str) -> List[str]:
        """从代码行中提取函数调用"""
        matches = self.function_pattern.findall(line)
        return matches
