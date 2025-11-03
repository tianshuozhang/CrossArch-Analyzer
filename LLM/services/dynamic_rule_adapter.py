import logging
from typing import Dict, Any, List

# 假设的 RuleEngine 和 MemoryManager 的简化接口
# 我们无法直接导入它们，但在这里定义接口以便于理解
class MockRuleEngine:
    def add_temp_rule(self,
                      rule_type: str,
                      pattern: str,
                      architecture: str,
                      confidence: float,
                      source: str):
        pass # 在真实 RuleEngine 中实现此方法
    
    def update_weight(self, pattern: str, new_weight: float):
        pass # 在真实 RuleEngine 中实现此方法

class MockMemoryManager:
    def get_project_history(self, project_id: str) -> Dict[str, Any]:
        return {"frequent_custom_macros": {}} 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicRuleAdapter:
    """
    动态规则适配器。
    根据项目的历史分析数据和构建系统上下文，动态调整规则引擎的规则，
    以提高对特定项目编码风格的适应性和分析准确性。
    """

    def __init__(self, rule_engine: MockRuleEngine, memory_manager: MockMemoryManager, project_id: str):
        """
        初始化适配器。

        Args:
            rule_engine: 当前会话的规则引擎实例。
            memory_manager: 用于访问历史数据的内存管理器实例。
            project_id: 当前正在分析的项目的唯一标识符。
        """
        self.rule_engine = rule_engine
        self.memory_manager = memory_manager
        self.project_id = project_id
        logger.info(f"动态规则适配器已为项目 '{project_id}' 初始化。")

    def adapt_rules_from_context(self, build_context: Dict[str, Any]):
        """
        根据构建系统分析出的全局宏，添加高置信度的临时规则。

        Args:
            build_context (Dict[str, Any]): 从 BuildSystemAnalyzer 获取的上下文。
                                            例如: {"definitions": {"USE_NEON", "IS_X86_BUILD"}}
        """
        global_definitions = build_context.get("definitions", set())
        if not global_definitions:
            return

        logger.info("正在根据构建系统上下文调整规则...")
        for macro in global_definitions:
            # 简单示例：如果宏名包含'NEON'或'ARM'，就认为是ARM特征
            if any(keyword in macro.upper() for keyword in ['ARM', 'NEON', 'AARCH64']):
                self.rule_engine.add_temp_rule(
                    rule_type='preprocessor',
                    pattern=macro,
                    architecture='ARM',
                    confidence=0.95,  # 非常高的置信度，因为它来自构建系统
                    source='dynamic_adapter:build_context'
                )
                logger.info(f"添加临时规则：宏 '{macro}' -> ARM (置信度 0.95)")
            # 可以继续添加其他架构的启发式规则...

    def adapt_rules_from_history(self):
        """
        根据 MemoryManager 中存储的项目历史分析数据，学习新的规则。
        例如，发现某个自定义宏总是在ARM代码块中出现。
        """
        project_history = self.memory_manager.get_project_history(self.project_id)
        frequent_macros = project_history.get("frequent_custom_macros", {})
        
        if not frequent_macros:
            return
            
        logger.info("正在根据项目分析历史调整规则...")
        # frequent_macros 示例: {'PROJ_FAST_PATH_AARCH64': {'arch': 'ARM', 'count': 50}}
        for macro, info in frequent_macros.items():
            arch = info.get('arch')
            count = info.get('count', 0)
            
            # 如果一个宏在某个架构中出现超过一定次数（例如10次），就将其视为一个特征
            if arch and count > 10:
                # 置信度可以与出现次数相关
                confidence = min(0.5 + count * 0.01, 0.9) 
                self.rule_engine.add_temp_rule(
                    rule_type='preprocessor',
                    pattern=macro,
                    architecture=arch,
                    confidence=confidence,
                    source='dynamic_adapter:history'
                )
                logger.info(f"添加临时规则：历史宏 '{macro}' -> {arch} (置信度 {confidence:.2f})")