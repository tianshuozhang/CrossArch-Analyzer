from typing import Dict, List, Tuple, Any, Optional
import json

# 导入核心功能模块（假设它们位于同一目录或已在PYTHONPATH中）
# 注意：在实际项目中，您可能需要确保这些模块已正确导入。
from core.static_classify_tool import StaticClassifyTool
from core.symbol_tagger import SymbolTagger
from core.target_tagger import TargetTagger

class Static_CodeAnalyzer:
    """
    集成 C/C++ 静态分析、符号关联和体系结构标记的工具类。
    """
    
    def __init__(self):
        """
        初始化分析器。
        （如果 StaticClassifyTool 需要初始化参数，可以在此处添加）
        """
        pass

    def scan_code(self, code: str) -> Tuple[Optional[Dict[str, Any]], Optional[List[str]]]:
        """
        对输入的 C/C++ 源代码运行完整的分析和标记流程。

        Args:
            code: 待分析的 C/C++ 源代码字符串。

        Returns:
            一个包含以下元素的元组 (Tuple)：
            - result: 包含最终标记结果的字典 (Dict)，如果解析失败则为 None。
                      成功时，该字典将包含 'symbols', 'tagTarget_outerSymbol_dict' 
                      等 StaticClassifyTool 的原始输出，以及新增的 'taggedTargets' 
                      (代码块标记结果)。
            - errors: 解析失败时的错误行号列表 (List[str])，成功则为 None。
        """
        print("--- 1. 静态代码分析与符号关联 (StaticClassifyTool) ---")
        
        # 1. 静态分析与符号关联：获取所有符号和代码块间的引用关系
        analysis_result, error_lines = StaticClassifyTool.scan_code(code)

        if error_lines is not None:
            print(f"❌ 代码解析失败，错误发生在以下行：{error_lines}")
            return None, error_lines

        symbols_list = analysis_result["symbols"]
        tagTarget_outerSymbol_dict = analysis_result["tagTarget_outerSymbol_dict"]

        print(f"分析成功。提取的符号数量: {len(symbols_list)}")
        print("-------------------------------------------------------")

        # 2. 符号体系结构标记 (SymbolTagger)
        print("--- 2. 符号体系结构标记 (SymbolTagger) ---")
        
        # 使用 SymbolTagger 标记每个符号的体系结构
        # ⚠️ 注意：如果 SymbolTagger.tag 方法不是静态方法，这里需要实例化 SymbolTagger()
        # 假设 SymbolTagger.tag 是静态方法，或通过类名调用
        taggedSymbols: Dict[str, str] = SymbolTagger.tag(symbols_list)
        
        relevant_tags = sum(1 for arch in taggedSymbols.values() if arch != "irrelevant")
        print(f"符号标记完成。发现与体系结构相关的符号数量: {relevant_tags}")
        print("-------------------------------------------------------")
        
        # 3. 代码块体系结构标记 (TargetTagger)
        print("--- 3. 代码块体系结构标记 (TargetTagger) ---")
        
        # 使用 TargetTagger 标记每个代码块，集合其引用的所有符号的体系结构标签
        # 假设 TargetTagger.tag 是静态方法，或通过类名调用
        taggedTargets: List[Tuple[str, Tuple[int, int], List[str]]] = TargetTagger.tag(
            tagTarget_outerSymbol_dict, 
            taggedSymbols
        )
        
        print(f"代码块标记完成。共标记 {len(taggedTargets)} 个代码块。")
        print("-------------------------------------------------------")

        # 4. 整合结果
        analysis_result["taggedSymbols"] = taggedSymbols  # 可选：将标记后的符号也加入结果
        analysis_result["taggedTargets"] = taggedTargets
        
        # 打印最终结果示例
        # self._print_summary(taggedTargets)

        return analysis_result, None
    
    def _print_summary(self, taggedTargets: List[Tuple[str, Tuple[int, int], List[str]]]):
        """打印最终标记结果的摘要。"""
        print("\n--- 最终代码块标记结果 (Top 5 示例) ---")
        if not taggedTargets:
            print("未发现需要标记的代码块。")
            return
            
        for tagTarget, lineRange, archs in taggedTargets[:5]:
            # 格式化输出，lineRange 是 (start_line, end_line)
            line_str = f"行 {lineRange[0]}~{lineRange[1]}" if lineRange[0] != lineRange[1] else f"行 {lineRange[0]}"
            print(f"[{line_str}]: '{tagTarget}' -> 体系结构: {archs}")
        
        if len(taggedTargets) > 5:
            print(f"... 还有 {len(taggedTargets) - 5} 个代码块未显示")

# --- 示例调用 ---
if __name__ == "__main__":
    code = """#include <stdio.h>
// 多架构支持示例
#if !defined(__arm__)
    #define ARCH_NAME "ARM"
    #define ARCH_FEATURE "NEON"
#elif defined(__x86_64__) 
    #define ARCH_NAME "x86_64" __attribute__((__riscv))
    #define ARCH_FEATURE "SSE/AVX"
#elif defined(__riscv) 
    #define ARCH_NAME "RISC-V" __attribute__((test))
    #define ARCH_FEATURE "V Extension"
#else
    #define ARCH_NAME "Unknown"
    #define ARCH_FEATURE "Generic"
#endif
[[no_unique_address]] T payload;
int main() {
    int a = 10;
    printf("Architecture: %s\\n", ARCH_NAME);
    printf("Feature: %s\\n", ARCH_FEATURE);
    
    // 条件编译的不同实现
    #ifdef __arm__
        asm("mov r0, #42");
        _asm("mov r0, #42");
        __asm("mov r0, #42");
    #elif defined(__x86_64__)
        asm("mov $42, %eax");
    #endif
    
    return 0;
}
    """

    analyzer = Static_CodeAnalyzer()
    save = False
    # 运行分析
    final_result, errors = analyzer.scan_code(code)
    
    if final_result:
        # 示例：将代码块的标记结果保存为 JSON
        print("\n✅ 代码分析与标记完成。")
        if save:
            with open("tagged_targets_output.json", "w", encoding='utf-8') as f:
                # 只导出关键的标记部分
                json.dump(final_result["taggedTargets"], f, indent=4, ensure_ascii=False)
            print("\n✅ 完整标记结果已保存到 tagged_targets_output.json (仅包含代码块标记部分)")