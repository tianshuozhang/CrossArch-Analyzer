from algo_framework.utils.data_structures import *
import algo_framework.utils.project_helper as ph
from algo_framework.utils.symbol_tagger import tag_symbol

import networkx as nx


class CodeAnalyzer:

    @staticmethod
    def analyze_symbol_relations(
        symbol_relations: list[DepRelation], tagTarget_relations: list[DepRelation]
    ):
        G = nx.DiGraph()
        nodes: dict[str, CodeNode] = {}

        def _prepare():
            for symbol_relation in symbol_relations:
                nodes.setdefault(symbol_relation.node.name, symbol_relation.node)
                for dependency in symbol_relation.dependencies:
                    nodes.setdefault(dependency.name, dependency)
            for tagTarget_relation in tagTarget_relations:
                for dependency in tagTarget_relation.dependencies:
                    nodes.setdefault(dependency.name, dependency)
            for symbol_relation in symbol_relations:
                G.add_edges_from(
                    [
                        (dependence.name, symbol_relation.node.name)
                        for dependence in symbol_relation.dependencies
                    ]
                )

        _prepare()

        def remove_cycles(G):
            """原地修改图 G，移除边直到无环（简单粗暴版）"""
            while True:
                try:
                    # 尝试找一个环
                    cycle = nx.find_cycle(G, orientation="original")
                    # 粗暴策略：删除环中的最后一条边（或第一条）
                    u, v = cycle[-1][:2]  # 取最后一个边 (u -> v)
                    print(f"Removing edge {u} -> {v} to break cycle")
                    G.remove_edge(u, v)
                except nx.NetworkXNoCycle:
                    break  # 无环了，退出

        remove_cycles(G)

        def _broadcast():
            for name in nx.topological_sort(G):
                node = nodes[name]
                tag_symbol(node)
                for pred_name in G.predecessors(name):
                    pred_node = nodes[pred_name]
                    node.archs |= pred_node.archs

        _broadcast()
        pass

    @staticmethod
    def analyze(
        file_paths: list[str],
        file_tagTarget_relations: FileResultDict[list[DepRelation]],
        file_tree_sitter_analysis_result: FileResultDict[TreeSitterAnalysisResult],
        _,
    ) -> FileResultDict[dict[tuple[int, int], set[str]]]:
        def merge_tagTarget_relations(args):
            tagTarget_relations, tree_sitter_analysis_result = args
            merged_tagTarget_relations = (
                tree_sitter_analysis_result.tagTarget_relations + tagTarget_relations
            )
            merged_symbol_relations = tree_sitter_analysis_result.symbol_relations
            return merged_tagTarget_relations, merged_symbol_relations

        file_tagTarget_relations, file_symbol_relations = ph.map_out_tuple(
            file_paths,
            merge_tagTarget_relations,
            file_tagTarget_relations,
            file_tree_sitter_analysis_result,
        )
        CodeAnalyzer.analyze_symbol_relations(
            ph.de_file_and_merge(file_symbol_relations),
            ph.de_file_and_merge(file_tagTarget_relations),
        )

        def _make_tagTarget_arch_dict(args: tuple):
            (tagTarget_relations,) = args
            arch_dict = {}
            for tagTarget_relation in tagTarget_relations:
                k = (
                    tagTarget_relation.node.info.start_line,
                    tagTarget_relation.node.info.end_line,
                )
                v = set().union(
                    *(node.archs for node in tagTarget_relation.dependencies)
                )
                arch_dict[k] = v
            return arch_dict

        AnalysisResult = ph.map(
            file_paths,
            _make_tagTarget_arch_dict,
            file_tagTarget_relations,
        )

        return AnalysisResult
