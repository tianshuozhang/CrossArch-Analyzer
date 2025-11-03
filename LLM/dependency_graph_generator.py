import logging
from typing import Dict, Any, List
from LLM.services.cross_file_correlator import CrossFileCorrelator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 可视化配置 ---
# 为不同架构和实体定义颜色，便于前端区分
COLOR_MAP = {
    'ARM': '#F56C6C',
    'x86': '#409EFF',
    'RISC-V': '#67C23A',
    'MIPS': '#E6A23C',
    'LoongArch': '#573587', # LoongISA -> LoongArch
    'PowerPC': '#909399',
    'Generic': '#B0B0B0', # 架构无关
    'File': '#303133',    # 文件节点
    'Missing': '#FF00FF', # 用于标记缺失的链接
}

NODE_CATEGORIES = {
    'File': 0, 'ARM': 1, 'x86': 2, 'RISC-V': 3, 'Generic': 4,
    'MIPS': 5, 'LoongArch': 6, 'PowerPC': 7
}

class DependencyGraphGenerator:
    """
    将 CrossFileCorrelator 的分析结果转换为 ECharts 的图谱数据格式。
    """

    def __init__(self, correlator: CrossFileCorrelator):
        """
        初始化生成器。

        Args:
            correlator: 一个已经执行过分析的 CrossFileCorrelator 实例。
        """
        self.correlator = correlator
        # 确保 correlator 已经构建了符号表
        if not self.correlator.symbol_table:
            self.correlator._build_symbol_table()
        
        self.nodes = []
        self.links = []
        self.node_names = set() # 用于避免重复添加节点

    def _add_node(self, name: str, category_name: str, symbol_size: int, value: Any = None):
        """辅助函数，用于添加一个唯一的节点。"""
        if name not in self.node_names:
            self.nodes.append({
                "name": name,
                "value": value or name,
                "symbolSize": symbol_size,
                "category": NODE_CATEGORIES.get(category_name, -1),
            })
            self.node_names.add(name)

    def _add_link(self, source: str, target: str, line_style: Dict = None):
        """辅助函数，用于添加一条边。"""
        self.links.append({
            "source": source,
            "target": target,
            "lineStyle": line_style or {"width": 1}
        })

    def generate_graph_data(self) -> Dict[str, Any]:
        """
        生成完整的 ECharts 图谱数据。

        Returns:
            一个包含 nodes, links, categories 的字典，可直接序列化为JSON供前端使用。
        """
        logger.info("开始生成依赖关系图谱数据...")

        # --- 1. 添加节点 ---
        # 为每个文件创建一个大节点
        all_files = {report['file_path'] for report in self.correlator.all_reports}
        for file_path in all_files:
            self._add_node(name=file_path, category_name='File', symbol_size=30)
            
        # 为每个函数-架构组合创建一个节点
        for func_name, implementations in self.correlator.symbol_table.items():
            for arch, file_path in implementations.items():
                # 节点名格式: "函数名(架构)"，确保唯一性
                node_name = f"{func_name}({arch})"
                self._add_node(name=node_name, category_name=arch, symbol_size=15, value=func_name)
                # 添加从文件到其定义的函数的链接
                self._add_link(source=file_path, target=node_name)

        # --- 2. 添加函数调用链接 ---
        for callee_func, caller_files in self.correlator.call_graph.items():
            for caller_file in set(caller_files):
                # 调用关系：从文件节点指向它调用的所有可能的函数实现
                implementations = self.correlator.symbol_table.get(callee_func, {})
                for arch, _ in implementations.items():
                    target_node_name = f"{callee_func}({arch})"
                    self._add_link(source=caller_file, target=target_node_name)

        # --- 3. 高亮显示缺失的实现 (核心价值) ---
        missing_issues = self.correlator.find_missing_implementations()
        for issue in missing_issues:
            func_name = issue['function_name']
            called_from_files = issue['called_from']
            missing_archs = issue['missing_for_arch']
            
            for caller_file in called_from_files:
                for missing_arch in missing_archs:
                    # 添加一条从调用文件到 "缺失" 节点的虚线/高亮边
                    missing_node_name = f"{func_name}({missing_arch} - MISSING)"
                    self._add_node(name=missing_node_name, category_name='Generic', symbol_size=10)
                    
                    self._add_link(
                        source=caller_file,
                        target=missing_node_name,
                        line_style={
                            "width": 2,
                            "type": "dashed",
                            "color": COLOR_MAP['Missing']
                        }
                    )
        
        # --- 4. 构建最终输出 ---
        categories_for_echarts = [
            {"name": name, "itemStyle": {"color": COLOR_MAP.get(name, '#000')}}
            for name in NODE_CATEGORIES.keys()
        ]
        
        logger.info(f"图谱数据生成完成: {len(self.nodes)} 个节点, {len(self.links)} 条边。")
        return {
            "nodes": self.nodes,
            "links": self.links,
            "categories": categories_for_echarts
        }