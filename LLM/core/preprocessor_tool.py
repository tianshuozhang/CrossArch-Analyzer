import re
from typing import List, Dict, Any

class PreprocessorTool:
    """C/C++预处理宏扫描器工具"""
    
    def __init__(self, arch_macros: Dict[str, List[str]]):
        self.arch_macros = arch_macros
        self.directive_pattern = re.compile(
            r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b',
            re.MULTILINE
        )
        self.macro_pattern = re.compile(
            r'defined\s*\(\s*(\w+)\s*\)|(\b\w+\b)',
            re.MULTILINE
        )
    
    def scan_code(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
        """
        扫描代码中的预处理指令和架构相关宏
        
        Args:
            code: C/C++源代码字符串
            file_path: 源代码文件路径
            
        Returns:
            架构代码块的结构化列表
        """
        lines = code.split('\n')
        results = []
        stack = []  # 用于跟踪预处理块嵌套
        current_block = None
        line_number = 0
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # 检查预处理指令
            if line.startswith('#'):
                directive_match = self.directive_pattern.match(line)
                if directive_match:
                    directive = directive_match.group(1)
                    self._process_directive(
                        directive, line, i, stack, current_block, results
                    )
            
            # 在当前活动块中检查架构宏
            if stack and stack[-1]['active']:
                arch = self._detect_arch_from_line(line)
                if arch and current_block:
                    current_block['arch'] = arch
                    current_block['end_line'] = i
            
            line_number = i
        
        return results
    
    def _process_directive(self, directive: str, line: str, line_num: int, 
                         stack: List, current_block: Dict, results: List):
        """处理具体的预处理指令"""
        if directive in ['if', 'ifdef', 'ifndef']:
            # 开始新的条件块
            arch = self._detect_arch_from_line(line)
            new_block = {
                'start_line': line_num,
                'end_line': line_num,
                'arch': arch,
                'directive': directive,
                'active': True,
                'nested_level': len(stack)
            }
            stack.append(new_block)
            
        elif directive == 'elif':
            if stack:
                stack[-1]['active'] = False
                arch = self._detect_arch_from_line(line)
                new_block = {
                    'start_line': line_num,
                    'end_line': line_num,
                    'arch': arch,
                    'directive': directive,
                    'active': True,
                    'nested_level': len(stack) - 1
                }
                stack.append(new_block)
                
        elif directive == 'else':
            if stack:
                stack[-1]['active'] = False
                new_block = {
                    'start_line': line_num,
                    'end_line': line_num,
                    'arch': 'ELSE_BLOCK',
                    'directive': directive,
                    'active': True,
                    'nested_level': len(stack) - 1
                }
                stack.append(new_block)
                
        elif directive == 'endif':
            if stack:
                completed_block = stack.pop()
                completed_block['end_line'] = line_num
                if completed_block['arch']:
                    results.append(completed_block)
    
    def _detect_arch_from_line(self, line: str) -> str:
        """从代码行中检测架构宏"""
        for arch, macros in self.arch_macros.items():
            for macro in macros:
                if re.search(r'\b' + re.escape(macro) + r'\b', line):
                    return arch
        return None
