import re
from typing import List, Dict, Any

class AsmQueryTool:
    """内联汇编代码提取器工具"""
    
    def __init__(self):
        # 匹配各种风格的内联汇编
        self.asm_patterns = [
            # GNU风格: __asm__("instruction")
            re.compile(r'__asm__\s*\(\s*"([^"]+)"\s*\)', re.MULTILINE),
            # MSVC风格: __asm { instruction }
            re.compile(r'__asm\s*\{([^}]+)\}', re.MULTILINE | re.DOTALL),
            # 简单asm关键字
            re.compile(r'\basm\s*\(\s*"([^"]+)"\s*\)', re.MULTILINE),
        ]
        
        # 架构特定的汇编指令模式
        self.arch_instructions = {
            "ARM": ["ldr", "str", "add", "sub", "mul", "bne", "beq", "bx"],
            "x86": ["mov", "add", "sub", "jmp", "call", "push", "pop"],
            "RISC-V": ["lw", "sw", "add", "sub", "jal", "jr"],
            "MIPS": ["lw", "sw", "add", "sub", "beq", "bne"],
            "PowerPC": ["lwz", "stw", "add", "subf", "bne", "beq"]
        }
    
    def extract_inline_asm(self, code: str) -> List[Dict[str, Any]]:
        """
        从C/C++代码中提取内联汇编
        
        Args:
            code: 源代码字符串
            
        Returns:
            内联汇编块的结构化列表
        """
        results = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            asm_content = self._extract_asm_from_line(line)
            if asm_content:
                arch = self._identify_arch_from_asm(asm_content)
                results.append({
                    'line_number': line_num,
                    'type': 'inline_asm',
                    'content': asm_content,
                    'arch': arch,
                    'original_line': line.strip()
                })
        
        return results
    
    def _extract_asm_from_line(self, line: str) -> str:
        """从单行代码中提取汇编内容"""
        for pattern in self.asm_patterns:
            match = pattern.search(line)
            if match:
                # 返回第一个捕获组的内容
                return match.group(1).strip()
        return None
    
    def _identify_arch_from_asm(self, asm_content: str) -> str:
        """根据汇编指令识别架构"""
        for arch, instructions in self.arch_instructions.items():
            for instruction in instructions:
                if re.search(r'\b' + instruction + r'\b', asm_content, re.IGNORECASE):
                    return arch
        return "Unknown"
