import clang.cindex
from typing import List, Dict, Any, Tuple

# clang.cindex.Config.set_library_path('/path/to/your/llvm/lib')

class FunctionParserTool:
    """使用 libclang 解析C/C++代码，提取函数定义和调用。"""

    def parse_functions(self, code: str, file_path: str) -> Tuple[List[Dict], List[Dict]]:
        """
        解析源代码，返回定义的函数和调用的函数列表。

        Returns:
            A tuple containing (defined_functions, called_functions).
        """
        index = clang.cindex.Index.create()
        # 使用虚拟文件名，避免读写文件系统
        tu = index.parse(file_path, args=['-x', 'c++'], unsaved_files=[(file_path, code)])

        defined_functions = []
        called_functions = []

        # 遍历AST
        for node in tu.cursor.walk_preorder():
            # 找到函数定义
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL and node.is_definition():
                defined_functions.append({
                    "name": node.spelling,
                    "line_number": node.location.line
                    # 'architecture' 将在后续agent中关联
                })
            
            # 找到函数调用
            elif node.kind == clang.cindex.CursorKind.CALL_EXPR:
                called_functions.append({
                    "name": node.spelling,
                    "line_number": node.location.line
                })
                
        return defined_functions, called_functions
