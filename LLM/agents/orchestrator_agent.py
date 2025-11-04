from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List
import json

from core.preprocessor_tool import PreprocessorTool
from core.asm_query_tool import AsmQueryTool
from core.intrinsics_tool import IntrinsicsTool
from core.rule_engine import RuleEngine
from config import ARCH_MACROS, INTRINSICS_MAPPING
from function_parser_tool import FunctionParserTool

class OrchestratorAgent:
    """主控智能体：负责任务分解和工具编排"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm = ChatOpenAI(**llm_config)
        
        # 初始化工具
        self.preprocessor_tool = PreprocessorTool(ARCH_MACROS)
        self.asm_tool = AsmQueryTool()
        self.intrinsics_tool = IntrinsicsTool(INTRINSICS_MAPPING)
        self.rule_engine = RuleEngine()
        self.function_parser = FunctionParserTool()

        # 系统提示词
        self.system_prompt = SystemMessage(content="""
        你是一个专业的代码架构分析引擎。你的任务是将C/C++代码按指令集架构分类。
        
        你必须严格按照以下步骤执行：
        1. 首先调用预处理宏扫描器分析代码中的条件编译指令
        2. 然后调用内联汇编提取器识别架构相关的汇编代码
        3. 接着调用内置函数识别器检测架构特定的内置函数
        4. 最后基于规则引擎综合分析所有证据
        
        不要尝试自己阅读原始代码来分析架构特征，必须使用提供的工具。
        你的最终输出必须是严格的JSON格式。
        """)
    
    def analyze_code(self, code: str, file_path: str = "unknown.cpp") -> Dict[str, Any]:
        """
        分析代码的架构依赖关系
        
        Args:
            code: C/C++源代码
            file_path: 文件路径
            
        Returns:
            分析结果字典
        """
        # 步骤1: 预处理宏分析
        preprocessor_results = self.preprocessor_tool.scan_code(code, file_path)
        
        # 步骤2: 内联汇编分析
        asm_results = self.asm_tool.extract_inline_asm(code)
        
        # 步骤3: 内置函数分析
        intrinsics_results = self.intrinsics_tool.scan_intrinsics(code)
        
        # 步骤4: 规则推理
        classifications = self.rule_engine.classify_code(
            file_path, code, preprocessor_results, asm_results, intrinsics_results
        )
        
        # 步骤5: 生成结构化报告
        report = self._generate_report(classifications, file_path)
        
        return report
    
    def _generate_report(self, classifications: List, file_path: str) -> Dict[str, Any]:
        """生成结构化分析报告"""
        # 统计信息
        total_lines = len(classifications)
        arch_stats = {}
        
        for classification in classifications:
            arch = classification.category
            arch_stats[arch] = arch_stats.get(arch, 0) + 1
        
        # 构建详细结果
        detailed_results = []
        for classification in classifications:
            if classification.category != "Architecture-Independent":
                detailed_results.append({
                    "file_path": classification.file_path,
                    "line_number": classification.line_number,
                    "category": classification.category,
                    "reasoning": classification.reasoning,
                    "evidence": classification.evidence
                })
        
        return {
            "summary": {
                "total_lines_analyzed": total_lines,
                "architecture_statistics": arch_stats,
                "file_path": file_path
            },
            "detailed_results": detailed_results
        }
